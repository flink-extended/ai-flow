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
import abc
from datetime import datetime
from typing import List, Optional

from notification_service.model.event import Event


class ListenerRegistrationId(object):
    def __init__(self, id: str):
        self.id = id


class ListenerProcessor(object):
    def process(self, events: List[Event]):
        pass


class NotificationClient(metaclass=abc.ABCMeta):
    def __init__(self,
                 namespace: Optional[str] = None,
                 sender: Optional[str] = None):
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
                          event_keys: List[str] = None,
                          offset: int = None
                          ) -> ListenerRegistrationId:
        """
        Register a listener to listen events from Notification Server

        :param listener_processor: The processor of the listener.
        :param event_keys: Keys of event for listening. If not set, it will listen all events.
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
                    key: str = None,
                    namespace: str = None,
                    sender: str = None,
                    begin_offset: int = None,
                    end_offset: int = None) -> List[Event]:
        """
        List specific events in Notification Service.

        :param key: The key of the event to list.
        :param namespace: The namespace of the event to list.
        :param sender: The sender of the event to list.
        :param begin_offset: Offset of the events must be greater than this offset.
        :param end_offset: Offset of the events must be less than or equal to this offset.
        :return: The event list.
        """
        pass

    @abc.abstractmethod
    def time_to_offset(self, time: datetime) -> int:
        """
        Look up the biggest offset of the event whose create_time is
        less than or equal to the given timestamp.

        :return: The offset of the founded event.
        """
        pass
