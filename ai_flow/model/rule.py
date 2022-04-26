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
        :param condition:
        :param action:
        """
        self.condition = condition
        self.acton = action

    def trigger(self, event: Event, context: Context) -> Optional[TaskAction]:
        if self.condition.is_met(event, context):
            return self.acton
        else:
            return None


class WorkflowRule(object):
    """Rules that trigger workflow scheduling."""

    def __init__(self,
                 condition: Condition):
        """
        :param condition:
        """
        self.condition = condition

    def trigger(self, event: Event, context: Context) -> bool:
        if self.condition.is_met(event, context):
            return True
        else:
            return False
