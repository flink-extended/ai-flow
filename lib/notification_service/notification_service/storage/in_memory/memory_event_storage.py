#
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
#
import time
from collections import Iterable
from typing import Union, Tuple

from notification_service.model.event import ANY_CONDITION, Event
from notification_service.model.sender_event_count import SenderEventCount
from notification_service.storage.event_storage import BaseEventStorage


class MemoryEventStorage(BaseEventStorage):

    def __init__(self):
        self.store = []
        self.store_with_uuid = {}
        self.max_offset = 0
        self.clients = []

    def add_event(self, event: Event, uuid: str):
        self.max_offset += 1
        event.create_time = int(time.time() * 1000)
        event.offset = self.max_offset
        self.store.append(event)
        self.store_with_uuid[uuid] = event
        return event

    def list_events(self,
                    key: str = None,
                    namespace: str = None,
                    sender: str = None,
                    begin_offset: int = None,
                    end_offset: int = None):
        res = []
        key = None if key == "" else key
        namespace = None if namespace == "" else namespace
        sender = None if sender == "" else sender
        begin_offset = None if begin_offset == 0 else begin_offset
        end_offset = None if end_offset == 0 else end_offset

        for event in self.store:
            if key is not None and key != ANY_CONDITION and event.key != key:
                continue
            if namespace is not None and namespace != ANY_CONDITION and event.namespace != namespace:
                continue
            if sender is not None and sender != ANY_CONDITION and event.sender != sender:
                continue
            if begin_offset is not None and event.offset <= begin_offset:
                continue
            if end_offset is not None and event.offset > end_offset:
                continue
            res.append(event)
        return res

    def count_events(self,
                     key: str = None,
                     namespace: str = None,
                     sender: str = None,
                     begin_offset: int = None,
                     end_offset: int = None):
        key = None if key == "" else key
        namespace = None if namespace == "" else namespace
        sender = None if sender == "" else sender
        begin_offset = None if begin_offset == 0 else begin_offset
        end_offset = None if end_offset == 0 else end_offset
        event_counts = {}
        for event in self.store:
            if key is not None and key != ANY_CONDITION and event.key != key:
                continue
            if namespace is not None and namespace != ANY_CONDITION and event.namespace != namespace:
                continue
            if sender is not None and sender != ANY_CONDITION and event.sender != sender:
                continue
            if begin_offset is not None and event.offset <= begin_offset:
                continue
            if end_offset is not None and event.offset > end_offset:
                continue
            if event.sender in event_counts:
                event_counts.update({event.sender: event_counts.get(event.sender) + 1})
            else:
                event_counts.update({event.sender: 1})
        res = []
        for sender, event_count in event_counts.items():
            res.append(SenderEventCount(sender=sender, event_count=event_count))
        return res

    def list_all_events(self, start_time: int):
        res = []
        for event in self.store:
            if event.create_time >= start_time:
                res.append(event)
        return res

    def list_all_events_from_offset(self, start_offset: int, end_offset: int = None):
        res = []
        for event in self.store:
            if 0 < end_offset < event.offset:
                continue
            if event.offset > start_offset:
                res.append(event)
        return res

    def register_client(self, namespace: str = None, sender: str = None) -> int:
        self.clients.append((len(self.clients), namespace, sender))
        return len(self.clients) - 1

    def delete_client(self, client_id):
        try:
            self.clients.pop(client_id)
        except:
            pass

    def is_client_exists(self, client_id) -> bool:
        for item in self.clients:
            if item[0] == client_id:
                return True
        return False

    def get_event_by_uuid(self, uuid: str):
        return self.store_with_uuid.get(uuid)

    def timestamp_to_event_offset(self, timestamp: int) -> int:
        for e in self.store:
            if e.create_time > timestamp:
                return e.offset - 1
        return 0

    def clean_up(self):
        self.store.clear()
        self.clients.clear()
        self.store_with_uuid.clear()
        self.max_offset = 0
