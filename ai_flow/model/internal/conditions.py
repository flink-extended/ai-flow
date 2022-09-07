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
import json

from notification_service.model.event import Event
from typing import List

from ai_flow.model.condition import Condition
from ai_flow.model.context import Context
from ai_flow.model.internal.events import EventContextConstant, TaskStatusChangedEvent
from ai_flow.model.state import ValueState, ValueStateDescriptor
from ai_flow.model.status import TaskStatus


class SingleEventCondition(Condition):
    """The Condition that depend on a single event."""
    def __init__(self,
                 expect_event_key: str):
        """
        :param expect_event_key: The key of the event that this condition depends on.
        """
        super().__init__([expect_event_key])

    def is_met(self, event: Event, context: Context) -> bool:
        return True


def match_events(event_keys: List[str], event: Event) -> bool:
    for key in event_keys:
        if key == event.key:
            return True
    return False


class MeetAllCondition(Condition):
    """
    MeetAllCondition is a condition that contains multiple conditions,
    and it is satisfied when all of them are satisfied.
    """
    def __init__(self,
                 name: str,
                 conditions: List[Condition]):
        """
        :param name: The name of the MeetAllCondition.
                     It is used to create state and must be unique within the same workflow.
        :param conditions: The conditions that this condition contains.
        """
        events = []
        for c in conditions:
            events.extend(c.expect_event_keys)
        super().__init__(expect_event_keys=events)
        self.conditions = conditions
        self.name = name

    def is_met(self, event: Event, context: Context) -> bool:
        state: ValueState = context.get_state(ValueStateDescriptor(name=self.name))
        state_value = state.value()
        if state_value is None:
            state_value = [False] * len(self.conditions)
        for i in range(len(self.conditions)):
            if match_events(event_keys=self.conditions[i].expect_event_keys, event=event):
                if self.conditions[i].is_met(event, context):
                    state_value[i] = True
                else:
                    state_value[i] = False
        state.update(state_value)
        for v in state_value:
            if not v:
                return False
        return True


class MeetAnyCondition(Condition):
    """
    MeetAnyCondition is a condition that contains multiple conditions,
    and it is satisfied when any of them are satisfied.
    """
    def __init__(self, conditions: List[Condition]):
        """
        :param conditions: The conditions that this condition contains.
        """
        events = []
        for c in conditions:
            events.extend(c.expect_event_keys)
        super().__init__(expect_event_keys=events)
        self.conditions = conditions

    def is_met(self, event: Event, context: Context) -> bool:
        for condition in self.conditions:
            if match_events(event_keys=condition.expect_event_keys, event=event) and condition.is_met(event, context):
                return True
        return False


class TaskStatusCondition(Condition):
    """
    TaskStatusCondition is the condition of the event that the status of the dependent task changes.
    """
    def __init__(self,
                 workflow_name: str,
                 task_name: str,
                 namespace: str,
                 expect_status: TaskStatus
                 ):
        """
        :param workflow_name: The name of the workflow to which the task belongs.
        :param expect_status: Desired status of the task.
        """
        key = TaskStatusChangedEvent.generate_task_status_changed_event_key(
            namespace, workflow_name, task_name
        )
        super().__init__([key, ])
        self.expect_status = expect_status

    # todo: To judge whether to trigger or not,
    #  it is necessary to consider the inconsistency between the task status and the events.
    def is_met(self, event: Event, context: Context) -> bool:
        context_dict = json.loads(event.context)
        task_status = context_dict[EventContextConstant.TASK_STATUS]
        if self.expect_status == task_status:
            return True
        else:
            return False


class TaskStatusAllMetCondition(Condition):

    def __init__(self, condition_list: List[TaskStatusCondition]):
        """
        :param condition_list: The conditions that this condition contains.
        """
        events = []
        for c in condition_list:
            events.extend(c.expect_event_keys)
        super().__init__(expect_event_keys=events)
        self.condition_list = condition_list

    def is_met(self, event: Event, context: Context) -> bool:
        namespace = context.workflow.namespace
        workflow_name = context.workflow.name
        for condition in self.condition_list:
            prefix = TaskStatusChangedEvent.event_key_prefix()
            index = len(f'{prefix}.{namespace}.{workflow_name}')
            event_key = condition.expect_event_keys[0]
            task_name = event_key[index+1:]
            task_status = context.get_task_status(task_name=task_name)
            if task_status != condition.expect_status:
                return False
        return True
