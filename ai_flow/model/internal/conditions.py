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


class MeetAllCondition(Condition):
    """
    MeetAllCondition is a condition that contains multiple conditions,
    and it is satisfied when all of them are satisfied.
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
            if not condition.is_met(event, context):
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
            if condition.is_met(event, context):
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
        :param task_name: The task's name.
        :param namespace: The task's namespace.
        :param expect_status: Desired status of the task.
        """
        super().__init__([TaskStatusChangedEventKey(workflow_name=workflow_name,
                                                    task_name=task_name,
                                                    namespace=namespace)])
        self.expect_status = expect_status

    def is_met(self, event: Event, context: Context) -> bool:
        status = context.get_task_status(task_name=self.expect_events[0].sender)
        if self.expect_status == status:
            return True
        else:
            return False
