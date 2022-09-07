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
from typing import List

from notification_service.model.member import Member


class HighAvailabilityStorage(ABC):

    @abstractmethod
    def list_living_members(self, ttl_ms) -> List[Member]:
        pass

    @abstractmethod
    def update_member(self, server_uri, server_uuid):
        pass

    @abstractmethod
    def clear_dead_members(self, ttl_ms):
        pass