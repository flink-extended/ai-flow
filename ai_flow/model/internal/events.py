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
from typing import Optional
import json
from notification_service.event import Event, EventKey, DEFAULT_NAMESPACE

from ai_flow.model.status import TaskStatus


class AIFlowEventType(object):
    """
    AIFlow internal event types.
    TASK_STATUS_CHANGED: Task instance running status changed type.
    """
    TASK_STATUS_CHANGED = 'TASK_STATUS_CHANGED'


class TaskStatusChangedEventKey(EventKey):
    """TaskStatusChangedEventKey represents an event of the task status changed."""
    def __init__(self,
                 workflow_name: str,
                 task_name: str,
                 namespace: str = DEFAULT_NAMESPACE):
        """
        :param workflow_name: The name of the workflow to which the task belongs.
        :param task_name: The task's name.
        :param namespace: The task's namespace.
        """
        super().__init__(namespace=namespace,
                         name=workflow_name,
                         event_type=AIFlowEventType.TASK_STATUS_CHANGED,
                         sender=task_name)


class TaskStatusChangedEvent(Event):
    """TaskStatusChangedEvent is an event of the task status changed."""
    def __init__(self,
                 workflow_name: str,
                 workflow_execution_id: int,
                 task_name: str,
                 status: TaskStatus,
                 namespace: str = DEFAULT_NAMESPACE):
        """
        :param workflow_name: The name of the workflow to which the task belongs.
        :param workflow_execution_id: Unique ID of WorkflowExecution.
        :param task_name: The task's name.
        :param status: The current status of the task.
        :param namespace: The task's namespace.
        """
        super().__init__(event_key=TaskStatusChangedEventKey(workflow_name=workflow_name,
                                                             task_name=task_name,
                                                             namespace=namespace),
                         message=status)
        self.context = json.dumps({'workflow_execution_id': workflow_execution_id})