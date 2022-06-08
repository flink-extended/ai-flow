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
from notification_service.event import EventKey, Event
from typing import List

from ai_flow.model.condition import Condition
from ai_flow.model.context import Context
from ai_flow.model.internal.events import TaskStatusChangedEventKey
from ai_flow.model.state import ValueState, ValueStateDescriptor
from ai_flow.model.status import TaskStatus


class SingleEventCondition(Condition):
    """The Condition that depend on a single event."""
    def __init__(self,
                 expect_event: EventKey):
        """
        :param expect_event: The event that this condition depends on.
        """
        super().__init__([expect_event])

    def is_met(self, event: Event, context: Context) -> bool:
        return True


def match_event(event_key: EventKey, event: Event) -> bool:
    if event_key.namespace is not None and event_key.namespace != event.event_key.namespace:
        return False
    if event_key.name is not None and event_key.name != event.event_key.name:
        return False
    if event_key.event_type is not None and event_key.event_type != event.event_key.event_type:
        return False
    if event_key.sender is not None and event_key.sender != event.event_key.sender:
        return False
    return True


def match_events(event_keys: List[EventKey], event: Event) -> bool:
    for ek in event_keys:
        if match_event(event_key=ek, event=event):
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
            events.extend(c.expect_events)
        super().__init__(expect_events=events)
        self.conditions = conditions
        self.name = name

    def is_met(self, event: Event, context: Context) -> bool:
        state: ValueState = context.get_state(ValueStateDescriptor(name=self.name))
        state_value = state.value()
        if state_value is None:
            state_value = [False] * len(self.conditions)
        for i in range(len(self.conditions)):
            if match_events(event_keys=self.conditions[i].expect_events, event=event):
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
            events.extend(c.expect_events)
        super().__init__(expect_events=events)
        self.conditions = conditions

    def is_met(self, event: Event, context: Context) -> bool:
        for condition in self.conditions:
            if match_events(event_keys=condition.expect_events, event=event) and condition.is_met(event, context):
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
        super().__init__([TaskStatusChangedEventKey(namespace=namespace,
                                                    workflow_name=workflow_name,
                                                    task_name=task_name)])
        self.expect_status = expect_status

    # todo: To judge whether to trigger or not,
    #  it is necessary to consider the inconsistency between the task status and the events.
    def is_met(self, event: Event, context: Context) -> bool:
        status = context.get_task_status(task_name=self.expect_events[0].sender)
        if self.expect_status == status:
            return True
        else:
            return False
