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
from ai_flow.model.state import StateDescriptor, State
from ai_flow.model.status import TaskStatus


class Context(object):
    """The context in which custom logic is executed."""

    def get_state(self, state_descriptor: StateDescriptor) -> State:
        """
        Get the State object.
        :param state_descriptor: Description of the State object.
        :return The State object.
        """
        pass

    def get_task_status(self, task_name) -> TaskStatus:
        """
        Get the task status by task name.
        :param task_name: The name of the task.
        """
        pass
