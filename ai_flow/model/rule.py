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
from notification_service.event import Event
from typing import Optional

from ai_flow.model.action import TaskAction
from ai_flow.model.condition import Condition
from ai_flow.model.context import Context


class TaskRule(object):
    """Rules that trigger task scheduling."""

    def __init__(self,
                 condition: Condition,
                 action: TaskAction):
        """
        :param condition: Trigger condition of the rule.
        :param action: The execution commands for scheduled tasks.
        """
        self.condition = condition
        self.action = action

    def trigger(self, event: Event, context: Context) -> Optional[TaskAction]:
        """
        Determine whether to trigger task scheduling behavior.
        :param event: The currently processed event.
        :param context: The context in which the rule is executed.
        :return None: Does not trigger task scheduling behavior.
                Not None: Execution command for scheduling the task.
        """
        if self.condition.is_met(event, context):
            return self.action
        else:
            return None


class WorkflowRule(object):
    """Rules that trigger workflow scheduling."""

    def __init__(self,
                 condition: Condition):
        """
        :param condition: Trigger condition of the rule.
        """
        self.condition = condition

    def trigger(self, event: Event, context: Context) -> bool:
        """
        Determine whether to trigger workflow running.
        :param event: The currently processed event.
        :param context: The context in which the rule is executed.
        :return True:Start a WorkflowExecution. False: Do not start a WorkflowExecution.
        """
        if self.condition.is_met(event, context):
            return True
        else:
            return False
