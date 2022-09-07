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
from abc import ABC, abstractmethod

from notification_service.model.event import Event


class BaseEventStorage(ABC):

    @abstractmethod
    def add_event(self, event: Event, uuid: str):
        pass

    @abstractmethod
    def list_events(self,
                    key: str = None,
                    namespace: str = None,
                    sender: str = None,
                    begin_offset: int = None,
                    end_offset: int = None):
        pass

    @abstractmethod
    def count_events(self,
                     key: str = None,
                     namespace: str = None,
                     sender: str = None,
                     begin_offset: int = None,
                     end_offset: int = None):
        pass

    @abstractmethod
    def clean_up(self):
        pass

    @abstractmethod
    def register_client(self, namespace: str = None, sender: str = None) -> int:
        pass

    @abstractmethod
    def delete_client(self, client_id):
        pass

    @abstractmethod
    def is_client_exists(self, client_id) -> bool:
        pass

    def get_event_by_uuid(self, uuid: str):
        pass

    def timestamp_to_event_offset(self, timestamp: int) -> int:
        pass
