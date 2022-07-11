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
from enum import Enum
import json
from notification_service.event import Event, EventKey, DEFAULT_NAMESPACE

from ai_flow.model.status import TaskStatus


class AIFlowEventType(object):
    """
    AIFlow internal event types.
    TASK_STATUS_CHANGED: Task instance running status changed type.
    AIFLOW_SCHEDULING_EVENT: Scheduling events defined by AIFlow.
    """
    TASK_STATUS_CHANGED = 'TASK_STATUS_CHANGED'
    AIFLOW_SCHEDULING_EVENT = 'AIFLOW_SCHEDULING_EVENT'


class SchedulingEventType(str, Enum):
    """
    SchedulingEventType is a scheduling event type defined by AIFlow.
    """
    START_WORKFLOW_EXECUTION = 'START_WORKFLOW_EXECUTION'
    STOP_WORKFLOW_EXECUTION = 'STOP_WORKFLOW_EXECUTION'
    START_TASK_EXECUTION = 'START_TASK_EXECUTION'
    STOP_TASK_EXECUTION = 'STOP_TASK_EXECUTION'
    RESTART_TASK_EXECUTION = 'RESTART_TASK_EXECUTION'
    PERIODIC_RUN_WORKFLOW = 'PERIODIC_RUN_WORKFLOW'
    PERIODIC_RUN_TASK = 'PERIODIC_RUN_TASK'
    TASK_STATUS = 'TASK_STATUS'
    TASK_HEARTBEAT_TIMEOUT = 'TASK_HEARTBEAT_TIMEOUT'


HAS_WORKFLOW_EXECUTION_ID_SET = {SchedulingEventType.STOP_WORKFLOW_EXECUTION,
                                 SchedulingEventType.START_TASK_EXECUTION,
                                 SchedulingEventType.RESTART_TASK_EXECUTION,
                                 SchedulingEventType.STOP_TASK_EXECUTION,
                                 SchedulingEventType.PERIODIC_RUN_TASK,
                                 SchedulingEventType.TASK_STATUS,
                                 SchedulingEventType.TASK_HEARTBEAT_TIMEOUT}


class EventContextConstant(object):
    NAMESPACE = 'namespace'
    WORKFLOW_NAME = 'workflow_name'
    WORKFLOW_ID = 'workflow_id'
    WORKFLOW_EXECUTION_ID = 'workflow_execution_id'
    TASK_NAME = 'task_name'
    TASK_EXECUTION_ID = 'task_execution_id'
    WORKFLOW_SCHEDULE_ID = 'workflow_schedule_id'
    WORKFLOW_SNAPSHOT_ID = 'workflow_snapshot_id'
    SEQUENCE_NUMBER = 'sequence_number'
    TASK_STATUS = 'task_status'


class TaskStatusChangedEventKey(EventKey):
    """TaskStatusChangedEventKey represents an event of the task status changed."""

    def __init__(self,
                 namespace: str,
                 workflow_name: str,
                 task_name: str):
        """
        :param workflow_name: The name of the workflow to which the task belongs.
        :param task_name: The task's name.
        """
        super().__init__(namespace=None,
                         name='{}.{}.{}'.format(namespace, workflow_name, task_name),
                         event_type=AIFlowEventType.TASK_STATUS_CHANGED,
                         sender=None)


class TaskStatusChangedEvent(Event):
    """TaskStatusChangedEvent is an event of the task status changed."""
    def __init__(self,
                 workflow_name: str,
                 workflow_execution_id: int,
                 task_name: str,
                 status: TaskStatus,
                 namespace: str):
        """
        :param workflow_name: The name of the workflow to which the task belongs.
        :param workflow_execution_id: Unique ID of WorkflowExecution.
        :param task_name: The task's name.
        :param status: The current status of the task.
        """
        super().__init__(event_key=TaskStatusChangedEventKey(workflow_name=workflow_name,
                                                             task_name=task_name,
                                                             namespace=namespace),
                         message="")
        self.context = json.dumps({EventContextConstant.NAMESPACE: namespace,
                                   EventContextConstant.WORKFLOW_EXECUTION_ID: workflow_execution_id,
                                   EventContextConstant.WORKFLOW_NAME: workflow_name,
                                   EventContextConstant.TASK_NAME: task_name,
                                   EventContextConstant.TASK_STATUS: status.value})


class SchedulingEvent(Event):
    """SchedulingEvent is a scheduling event defined by AIFlow"""
    def __init__(self, name, message):
        super().__init__(EventKey(namespace=None,
                                  sender=None,
                                  name=name,
                                  event_type=AIFlowEventType.AIFLOW_SCHEDULING_EVENT),
                         message)


class StartWorkflowExecutionEvent(SchedulingEvent):
    """StartWorkflowExecutionEvent is an event of starting a workflow execution."""

    def __init__(self, workflow_id, snapshot_id):
        super().__init__(SchedulingEventType.START_WORKFLOW_EXECUTION, None)
        self.context = json.dumps({EventContextConstant.WORKFLOW_ID: workflow_id,
                                   EventContextConstant.WORKFLOW_SNAPSHOT_ID: snapshot_id})


class StopWorkflowExecutionEvent(SchedulingEvent):
    """StopWorkflowExecutionEvent is an event of stopping a workflow execution."""

    def __init__(self, workflow_execution_id: int):
        super().__init__(SchedulingEventType.STOP_WORKFLOW_EXECUTION, None)
        self.context = json.dumps({EventContextConstant.WORKFLOW_EXECUTION_ID: workflow_execution_id})


class StartTaskExecutionEvent(SchedulingEvent):
    """StartTaskExecutionEvent is an event of starting a task execution."""

    def __init__(self, workflow_execution_id: int, task_name: str):
        super().__init__(SchedulingEventType.START_TASK_EXECUTION, None)
        self.context = json.dumps({EventContextConstant.WORKFLOW_EXECUTION_ID: workflow_execution_id,
                                   EventContextConstant.TASK_NAME: task_name})


class ReStartTaskExecutionEvent(SchedulingEvent):
    """ReStartTaskExecutionEvent is an event of restarting a task execution."""

    def __init__(self, workflow_execution_id: int, task_name: str):
        super().__init__(SchedulingEventType.RESTART_TASK_EXECUTION, None)
        self.context = json.dumps({EventContextConstant.WORKFLOW_EXECUTION_ID: workflow_execution_id,
                                   EventContextConstant.TASK_NAME: task_name})


class StopTaskExecutionEvent(SchedulingEvent):
    """StopTaskExecutionEvent is an event of stopping a task execution."""

    def __init__(self, workflow_execution_id: int, task_execution_id: int):
        super().__init__(SchedulingEventType.STOP_TASK_EXECUTION, None)
        self.context = json.dumps({EventContextConstant.WORKFLOW_EXECUTION_ID: workflow_execution_id,
                                   EventContextConstant.TASK_EXECUTION_ID: task_execution_id})


class PeriodicRunTaskEvent(SchedulingEvent):
    """PeriodicRunTaskEvent is an event of periodically starting a task."""

    def __init__(self,
                 workflow_execution_id: int,
                 task_name: str):
        """
        :param workflow_execution_id: The unique id of the workflow execution.
        :param task_name: The name of the task.
        """
        super().__init__(SchedulingEventType.PERIODIC_RUN_TASK, None)
        self.context = json.dumps({EventContextConstant.WORKFLOW_EXECUTION_ID: workflow_execution_id,
                                   EventContextConstant.TASK_NAME: task_name})


class PeriodicRunWorkflowEvent(SchedulingEvent):
    """PeriodicRunWorkflowEvent is an event of periodically starting a workflow."""

    def __init__(self,
                 workflow_id: int,
                 schedule_id: int):
        """
        :param schedule_id: The unique id of workflow schedule.
        """
        super().__init__(SchedulingEventType.PERIODIC_RUN_WORKFLOW, None)
        self.context = json.dumps({EventContextConstant.WORKFLOW_ID: workflow_id,
                                   EventContextConstant.WORKFLOW_SCHEDULE_ID: schedule_id})


class TaskStatusEvent(SchedulingEvent):
    """TaskStatusChangeEvent is an event of indicating a task execution's status changed."""

    def __init__(self,
                 workflow_execution_id: int,
                 task_name: str,
                 sequence_number: int,
                 status: TaskStatus):
        super().__init__(SchedulingEventType.TASK_STATUS, None)
        self.context = json.dumps({EventContextConstant.WORKFLOW_EXECUTION_ID: workflow_execution_id,
                                   EventContextConstant.TASK_NAME: task_name,
                                   EventContextConstant.SEQUENCE_NUMBER: sequence_number,
                                   EventContextConstant.TASK_STATUS: status.value})


class TaskHeartbeatTimeoutEvent(SchedulingEvent):
    """TaskHeartbeatTimeoutEvent is an event of indicating a task execution's heartbeat is timeout."""

    def __init__(self,
                 workflow_execution_id: int,
                 task_name: str,
                 sequence_number: int):
        super().__init__(SchedulingEventType.TASK_HEARTBEAT_TIMEOUT, None)
        self.context = json.dumps({EventContextConstant.WORKFLOW_EXECUTION_ID: workflow_execution_id,
                                   EventContextConstant.TASK_NAME: task_name,
                                   EventContextConstant.SEQUENCE_NUMBER: sequence_number})
