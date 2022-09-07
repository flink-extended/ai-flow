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
from typing import List

from notification_service.model.event import Event

from ai_flow.model.context import Context


class Condition(object):
    """Conditions that trigger scheduling."""
    def __init__(self,
                 expect_event_keys: List[str]):
        """
        :param expect_event_keys: The keys of events that this condition depends on.
        """
        self.expect_event_keys = expect_event_keys

    @abc.abstractmethod
    def is_met(self, event: Event, context: Context) -> bool:
        """
        Determine whether the condition is met.
        :param event: The currently processed event.
        :param context: The context in which the condition is executed.
        :return True:The condition is met. False: The condition is not met.
        """
        pass
