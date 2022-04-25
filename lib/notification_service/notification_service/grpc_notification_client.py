# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import logging
import os
import threading
from typing import List, Dict
from datetime import datetime
import grpc

from notification_service.event import Event, EventKey
from notification_service.notification_client import NotificationClient, ListenerRegistrationId, ListenerProcessor
from notification_service.proto import notification_service_pb2_grpc
from notification_service.proto.notification_service_pb2 \
    import SendEventRequest, ListEventsRequest, EventProto, ReturnStatus, ListAllEventsRequest, \
    RegisterClientRequest, ClientMeta, ClientIdRequest, TimeToOffsetRequest

NOTIFICATION_TIMEOUT_SECONDS = os.environ.get("NOTIFICATION_TIMEOUT_SECONDS", 5)


def event_proto_to_event(event_proto):
    event = Event(event_key=EventKey(name=event_proto.key,
                                     namespace=event_proto.namespace,
                                     event_type=event_proto.event_type,
                                     sender=event_proto.sender),
                  message=event_proto.value)
    event.context = event_proto.context
    event.offset = event_proto.version
    event.create_time = event_proto.create_time
    return event


class SequenceNumberManager(object):

    def __init__(self, seq_num: int = 0):
        self._lock = threading.RLock()
        self._seq_num = seq_num

    def increment_sequence_number(self):
        with self._lock:
            self._seq_num += 1

    def get_sequence_number(self):
        return self._seq_num


def filter_events(event_keys: List[EventKey], events: List[Event]) -> List[Event]:
    def match(event_key: EventKey, event: Event)->bool:
        if event_key.namespace is not None and event_key.namespace != event.event_key.namespace:
            return False
        if event_key.name is not None and event_key.name != event.event_key.name:
            return False
        if event_key.event_type is not None and event_key.event_type != event.event_key.event_type:
            return False
        if event_key.sender is not None and event_key.sender != event.event_key.sender:
            return False
        return True
    results = []
    for e in events:
        for k in event_keys:
            if match(k, e):
                results.append(e)
                break
    return results


class GrpcNotificationClient(NotificationClient):
    def __init__(self,
                 server_uri: str,
                 namespace: str,
                 sender: str,
                 client_id: int =None,
                 initial_seq_num: int = None
                 ):
        super().__init__(namespace, sender)
        self.server_uri = server_uri
        channel = grpc.insecure_channel(target=self.server_uri,
                                        options=[('grpc.max_receive_message_length', -1)])
        self.notification_stub = notification_service_pb2_grpc.NotificationServiceStub(channel)
        self.threads = {}  # type: Dict[int, threading.Thread]
        self.lock = threading.Lock()
        self._client_id = client_id
        self._initial_seq_num = initial_seq_num

        if self._client_id is None:
            request = RegisterClientRequest(
                client_meta=ClientMeta(namespace=self.namespace, sender=self.sender))
            response = self.notification_stub.registerClient(request)
            if response.return_code == ReturnStatus.SUCCESS:
                self._client_id = response.client_id
            else:
                raise Exception(response.return_msg)
        else:
            request = ClientIdRequest(client_id=self._client_id)
            response = self.notification_stub.isClientExists(request)
            if response.return_code != ReturnStatus.SUCCESS:
                raise Exception("Failed to close notification client: {}".format(self))
            elif not response.is_exists:
                raise Exception("Init notification client with a client id which have not registered.")
        seq_num = 0 if self._initial_seq_num is None else int(self._initial_seq_num)
        self.sequence_num_manager = SequenceNumberManager(seq_num)

    def close(self):
        if self._client_id is not None:
            request = ClientIdRequest(client_id=self._client_id)
            response = self.notification_stub.deleteClient(request)
            if response.return_code != ReturnStatus.SUCCESS:
                raise Exception("Failed to close notification client: {}".format(self))
        logging.info("The notification client:{} has been closed.".format(self))

    @property
    def client_id(self):
        """Int. Id of the Client."""
        return self._client_id

    @property
    def sequence_number(self):
        return self.sequence_num_manager.get_sequence_number()

    def send_event(self, event: Event):
        """
                Send event to Notification Service.

                :param event: the event updated.
                :return: The created event which has version and create time.
                """
        seq_num = self.sequence_num_manager.get_sequence_number()
        signature = '_'.join(['client', str(self._client_id), str(seq_num)])

        request = SendEventRequest(
            event=EventProto(
                key=event.event_key.name,
                value=event.message,
                event_type=event.event_key.event_type,
                context=event.context,
                namespace=self.namespace,
                sender=self.sender
            ),
            uuid=signature,
            enable_idempotence=True)
        response = self.notification_stub.sendEvent(request)
        if response.return_code == ReturnStatus.SUCCESS:
            self.sequence_num_manager.increment_sequence_number()
            return event_proto_to_event(response.event)
        else:
            raise Exception(response.return_msg)

    def register_listener(self,
                          listener_processor: ListenerProcessor,
                          event_keys: List[EventKey] = None,
                          offset: int = None) -> ListenerRegistrationId:

        def list_events_from_version(client, v, timeout_seconds: int = None):
            request = ListAllEventsRequest(start_version=v, timeout_seconds=timeout_seconds)
            response = client.notification_stub.listAllEvents(request)
            if response.return_code == ReturnStatus.SUCCESS:
                if response.events is None:
                    return None
                else:
                    events = []
                    for event_proto in response.events:
                        event = event_proto_to_event(event_proto)
                        events.append(event)
                    return events
            else:
                raise Exception(response.return_msg)

        def listen(client, v, p):
            t = threading.current_thread()
            current_version = 0 if v is None else v
            try:
                while getattr(t, '_flag', True):
                    notifications = list_events_from_version(client,
                                                             current_version,
                                                             NOTIFICATION_TIMEOUT_SECONDS)
                    if len(notifications) > 0:
                        if event_keys is not None:
                            events = filter_events(event_keys=event_keys, events=notifications)
                        else:
                            events = notifications
                        p.process(events)
                        current_version = notifications[len(notifications) - 1].offset
            except Exception as e:
                logging.exception("Exception when listening events, %s", e)
                raise e

        thread = threading.Thread(target=listen,
                                  args=(self, offset, listener_processor),
                                  daemon=True)
        thread.start()
        self.lock.acquire()
        try:
            self.threads[thread.__hash__()] = thread
        finally:
            self.lock.release()
        return ListenerRegistrationId(id=str(thread.__hash__()))

    def unregister_listener(self, id: ListenerRegistrationId):
        self.lock.acquire()
        key = int(id.id)
        try:
            if key in self.threads:
                thread = self.threads[key]
                thread._flag = False
                thread.join()
                del self.threads[key]
        finally:
            self.lock.release()

    def list_all_events(self,
                        start_time: int = None,
                        start_version: int = None,
                        end_version: int = None) -> List[Event]:
        """
        List specific `key` or `version` of events in Notification Service.

        :param start_time: (Optional) Start time of the events.
        :param start_version: (Optional) the version of the events must greater than the
                              start_version.
        :param end_version: (Optional) the version of the events must equal or less than the
                            end_version.
        :return: The event list.
        """
        request = ListAllEventsRequest(start_time=start_time,
                                       start_version=start_version,
                                       end_version=end_version)
        response = self.notification_stub.listAllEvents(request)
        if response.return_code == ReturnStatus.SUCCESS:
            if response.events is None:
                return []
            else:
                events = []
                for event_proto in response.events:
                    event = event_proto_to_event(event_proto)
                    events.append(event)
                return events
        else:
            raise Exception(response.return_msg)

    def list_events(self,
                    name: str = None,
                    namespace: str = None,
                    event_type: str = None,
                    sender: str = None,
                    offset: int = None) -> List[Event]:
        """
                List specific events in Notification Service.

                :param name: name of the event for listening.
                :param namespace: (Optional) Namespace of the event for listening.
                :param offset: (Optional) Offset of the events must greater than this version.
                :param event_type: (Optional) Type of the events.
                :param sender: The event sender.
                :return: The event list.
                """
        key = (name,)
        request = ListEventsRequest(
            keys=key,
            event_type=event_type,
            namespace=namespace,
            sender=sender,
            start_version=offset,
            start_time=None
        )
        response = self.notification_stub.listEvents(request)
        if response.return_code == ReturnStatus.SUCCESS:
            if response.events is None:
                return []
            else:
                events = []
                for event_proto in response.events:
                    event = event_proto_to_event(event_proto)
                    events.append(event)
                return events
        else:
            raise Exception(response.return_msg)

    def time_to_offset(self, time: datetime) -> int:
        timestamp = int(time.timestamp() * 1000)
        request = TimeToOffsetRequest(timestamp=timestamp)
        response = self.notification_stub.timestampToEventOffset(request)
        if response.return_code == ReturnStatus.SUCCESS:
            return response.offset
        else:
            raise Exception("There is no event whose create_time is greater than or equal to {}!".format(timestamp))
