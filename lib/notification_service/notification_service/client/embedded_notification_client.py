# Copyright 2022 The AI Flow Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
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
import time
import grpc
from functools import wraps
from random import shuffle
from datetime import datetime
from typing import List, Dict, Tuple


from notification_service.model.event import Event
from notification_service.client.notification_client import NotificationClient, ListenerRegistrationId, \
    ListenerProcessor
from notification_service.rpc.protobuf import notification_service_pb2_grpc
from notification_service.rpc.protobuf.notification_service_pb2 import SendEventRequest, \
    ListEventsRequest, CountEventsRequest, EventProto, ReturnStatus, ListAllEventsRequest, \
    RegisterClientRequest, ClientMeta, ClientIdRequest, TimeToOffsetRequest, ListMembersRequest
from notification_service.util.utils import event_proto_to_event, proto_to_member, sleep_and_detecting_running, \
    event_count_proto_to_event_count

from notification_service.model.sender_event_count import SenderEventCount

NOTIFICATION_TIMEOUT_SECONDS = os.environ.get("NOTIFICATION_TIMEOUT_SECONDS", 5)


class SequenceNumberManager(object):

    def __init__(self, seq_num: int = 0):
        self._lock = threading.RLock()
        self._seq_num = seq_num

    def increment_sequence_number(self):
        with self._lock:
            self._seq_num += 1

    def get_sequence_number(self):
        return self._seq_num


class EmbeddedNotificationClient(NotificationClient):
    def __init__(self,
                 server_uri: str,
                 namespace: str = None,
                 sender: str = None,
                 client_id: int = None,
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

        self.list_member_interval_ms = 1000
        self.retry_interval_ms = 1000
        self.retry_timeout_ms = 10000

        server_uri_list = self.server_uri.split(",")
        if len(server_uri_list) > 1:
            self.living_members = []
            self.current_uri = None
            last_error = None
            for server_uri in server_uri_list:
                channel = grpc.insecure_channel(server_uri)
                notification_stub = notification_service_pb2_grpc.NotificationServiceStub(channel)
                try:
                    request = ListMembersRequest(timeout_seconds=0)
                    response = notification_stub.listMembers(request)
                    if response.return_code == ReturnStatus.SUCCESS:
                        self.living_members = [proto_to_member(proto).server_uri
                                               for proto in response.members]
                    else:
                        raise Exception(response.return_msg)
                    self.current_uri = server_uri
                    self.notification_stub = notification_stub
                    break
                except grpc.RpcError as e:
                    last_error = e
            if self.current_uri is None:
                raise Exception("No available server uri!") from last_error
            self.ha_change_lock = threading.Lock()
            self.ha_running = True
            self.notification_stub = self._wrap_rpcs(self.notification_stub, server_uri)
            self.list_member_thread = threading.Thread(target=self._list_members, daemon=True)
            self.list_member_thread.start()

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

    def _ha_wrapper(self, func):
        @wraps(func)
        def call_with_retry(*args, **kwargs):
            current_func = getattr(self.notification_stub,
                                   func.__name__).inner_func
            start_time = time.time_ns() / 1000000
            failed_members = set()
            while True:
                try:
                    return current_func(*args, **kwargs)
                except grpc.RpcError:
                    logging.error("Exception thrown when calling rpc, change the connection.",
                                  exc_info=True)
                    with self.ha_change_lock:
                        # check the current_uri to ensure thread safety
                        if current_func.server_uri == self.current_uri:
                            living_members = list(self.living_members)
                            failed_members.add(self.current_uri)
                            shuffle(living_members)
                            found_new_member = False
                            for server_uri in living_members:
                                if server_uri in failed_members:
                                    continue
                                next_uri = server_uri
                                channel = grpc.insecure_channel(next_uri)
                                notification_stub = self._wrap_rpcs(
                                    notification_service_pb2_grpc.NotificationServiceStub(channel),
                                    next_uri)
                                self.notification_stub = notification_stub
                                current_func = getattr(self.notification_stub,
                                                       current_func.__name__).inner_func
                                self.current_uri = next_uri
                                found_new_member = True
                            if not found_new_member:
                                logging.error("No available living members currently. Sleep and retry.")
                                failed_members.clear()
                                sleep_and_detecting_running(self.retry_interval_ms,
                                                            lambda: self.ha_running)

                # break if stopped or timeout
                if not self.ha_running or \
                        time.time_ns() / 1000000 > start_time + self.retry_timeout_ms:
                    if not self.ha_running:
                        raise Exception("HA has been disabled.")
                    else:
                        raise Exception("Rpc retry timeout!")

        call_with_retry.inner_func = func
        return call_with_retry

    def _wrap_rpcs(self, stub, server_uri):
        for method_name, method in dict(stub.__dict__).items():
            method.__name__ = method_name
            method.server_uri = server_uri
            setattr(stub, method_name, self._ha_wrapper(method))
        return stub

    def _list_members(self):
        while self.ha_running:
            # refresh the living members
            request = ListMembersRequest(timeout_seconds=int(self.list_member_interval_ms / 1000))
            response = self.notification_stub.listMembers(request)
            if response.return_code == ReturnStatus.SUCCESS:
                with self.ha_change_lock:
                    self.living_members = [proto_to_member(proto).server_uri
                                           for proto in response.members]
            else:
                logging.error("Exception thrown when updating the living members: %s" %
                              response.return_msg)
            time.sleep(int(self.list_member_interval_ms / 1000))

    def disable_high_availability(self):
        if hasattr(self, "ha_running"):
            self.ha_running = False
            self.list_member_thread.join()

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
        :return: The created event which has offset and create time.
        """
        seq_num = self.sequence_num_manager.get_sequence_number()
        signature = '_'.join(['client', str(self._client_id), str(seq_num)])

        request = SendEventRequest(
            event=EventProto(
                key=event.key,
                value=event.value,
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
                          event_keys: List[str] = None,
                          offset: int = None) -> ListenerRegistrationId:

        def list_events_from_offset(client, v, timeout_seconds: int = None):
            request = ListAllEventsRequest(start_offset=v, timeout_seconds=timeout_seconds)
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
            current_offset = 0 if v is None else v
            try:
                while getattr(t, '_flag', True):
                    notifications = list_events_from_offset(client,
                                                            current_offset,
                                                            NOTIFICATION_TIMEOUT_SECONDS)
                    if len(notifications) > 0:
                        if event_keys is not None:
                            events = client.filter_events(event_keys=event_keys, events=notifications)
                        else:
                            events = notifications
                        p.process(events)
                        current_offset = notifications[len(notifications) - 1].offset
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

    def unregister_listener(self, registration_id: ListenerRegistrationId):
        self.lock.acquire()
        key = int(registration_id.id)
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
                        start_offset: int = None,
                        end_offset: int = None) -> List[Event]:
        """
        List the range of `offset` of events in Notification Service.

        :param start_time: (Optional) Start time of the events.
        :param start_offset: (Optional) the offset of the events must greater than the
                              start_offset.
        :param end_offset: (Optional) the offset of the events must equal or less than the
                            end_offset.
        :return: The event list.
        """
        request = ListAllEventsRequest(start_time=start_time,
                                       start_offset=start_offset,
                                       end_offset=end_offset)
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
                    key: str = None,
                    namespace: str = None,
                    sender: str = None,
                    begin_offset: int = None,
                    end_offset: int = None) -> List[Event]:
        """
        List specific events in Notification Service.

        :param key: Key of the event for listening.
        :param namespace: Namespace of the event for listening.
        :param sender: The event sender.
        :param begin_offset: Offset of the events must be greater than this offset.
        :param end_offset: Offset of the events must be less than or equal to this offset.
        :return: The event list.
        """
        request = ListEventsRequest(
            key=key,
            namespace=namespace,
            sender=sender,
            start_offset=begin_offset,
            end_offset=end_offset,
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
        return response.offset

    def count_events(self,
                     key: str = None,
                     namespace: str = None,
                     sender: str = None,
                     begin_offset: int = None,
                     end_offset: int = None) -> Tuple[int, List[SenderEventCount]]:
        """
        Count specific events in Notification Service.

        :param key: Key of the event for listening.
        :param namespace: Namespace of the event for listening.
        :param sender: The event sender.
        :param begin_offset: Offset of the events must be greater than this offset.
        :param end_offset: Offset of the events must be less than or equal to this offset.
        :return: The total event count and the list of event counts of each sender.
        """
        request = CountEventsRequest(
            key=key,
            namespace=namespace,
            sender=sender,
            start_offset=begin_offset,
            end_offset=end_offset,
        )
        response = self.notification_stub.countEvents(request)
        if response.return_code == ReturnStatus.SUCCESS:
            sender_event_counts = []
            for sender_event_count_proto in response.sender_event_counts:
                sender_event_count = event_count_proto_to_event_count(sender_event_count_proto)
                sender_event_counts.append(sender_event_count)
            return response.event_count, sender_event_counts
        else:
            raise Exception(response.return_msg)

    def filter_events(self, event_keys: List[str], events: List[Event]) -> List[Event]:
        def match(key, namespace, event: Event) -> bool:
            if key is not None and key != event.key:
                return False
            if namespace is not None and namespace != event.namespace:
                return False
            return True

        results = []
        for e in events:
            for k in event_keys:
                if match(k, self.namespace, e):
                    results.append(e)
                    break
        return results
