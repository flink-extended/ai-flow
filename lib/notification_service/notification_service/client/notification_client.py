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
import abc
from datetime import datetime
from typing import List

from notification_service.model.event import Event, EventKey


class ListenerRegistrationId(object):
    def __init__(self, id: str):
        self.id = id


class ListenerProcessor(object):
    def process(self, events: List[Event]):
        pass


class NotificationClient(metaclass=abc.ABCMeta):
    def __init__(self,
                 namespace: str,
                 sender: str):
        self.namespace = namespace
        self.sender = sender

    @abc.abstractmethod
    def send_event(self, event: Event):
        """
        Send event to Notification Sever.

        :param event: the event updated.
        :return: The created event.
        """
        pass

    @abc.abstractmethod
    def register_listener(self,
                          listener_processor: ListenerProcessor,
                          event_keys: List[EventKey] = None,
                          offset: int = None
                          ) -> ListenerRegistrationId:
        """
        Register a listener to listen events from Notification Server

        :param listener_processor: The processor of the listener.
        :param event_keys: EventKeys of notification for listening. If not set, it will listen all events.
        :param offset: The offset of the events to start listening.
        :return: The `ListenerRegistrationId` used to stop the listening.
        """
        pass

    @abc.abstractmethod
    def unregister_listener(self,
                            registration_id: ListenerRegistrationId):
        """
        Unregister the listener by id.
        """
        pass

    @abc.abstractmethod
    def list_events(self,
                    name: str = None,
                    namespace: str = None,
                    event_type: str = None,
                    sender: str = None,
                    offset: int = None,
                    ) -> List[Event]:
        """
        List specific events in Notification Service, if no parameter passed,
        all events would be listed.
        :return: List of query events.
        """
        pass

    @abc.abstractmethod
    def time_to_offset(self, time: datetime) -> int:
        """
        Look up the offset of the first event whose create_time is bigger the given timestamp
        :return: The offset of the founded event.
        """
        pass
