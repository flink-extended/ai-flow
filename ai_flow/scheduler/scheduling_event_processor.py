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
import logging
import json
from typing import Union

from notification_service.event import Event

from ai_flow.metadata.metadata_manager import MetadataManager
from ai_flow.model.action import TaskAction
from ai_flow.model.execution_type import ExecutionType
from ai_flow.model.internal.events import SchedulingEventType, EventContextConstant
from ai_flow.model.status import TaskStatus, TASK_ALIVE_SET
from ai_flow.model.task_execution import TaskExecutionKey
from ai_flow.scheduler.schedule_command import WorkflowExecutionScheduleCommand, \
    WorkflowExecutionStopCommand, WorkflowExecutionStartCommand, TaskScheduleCommand


class SchedulingEventProcessor(object):
    def __init__(self, metadata_manager: MetadataManager):
        self.metadata_manager = metadata_manager

    def process(self, event: Event) -> Union[WorkflowExecutionScheduleCommand,
                                             WorkflowExecutionStartCommand,
                                             WorkflowExecutionStopCommand]:
        scheduling_event_type = SchedulingEventType(event.event_key.name)
        context = json.loads(event.context)
        if SchedulingEventType.START_WORKFLOW_EXECUTION == scheduling_event_type:
            snapshot_id = context[EventContextConstant.WORKFLOW_SNAPSHOT_ID]
            return WorkflowExecutionStartCommand(snapshot_id=snapshot_id,
                                                 run_type=ExecutionType.MANUAL)
        elif SchedulingEventType.STOP_WORKFLOW_EXECUTION == scheduling_event_type:
            workflow_execution_id = context[EventContextConstant.WORKFLOW_EXECUTION_ID]
            return WorkflowExecutionStopCommand(workflow_execution_id=workflow_execution_id)
        elif SchedulingEventType.START_TASK_EXECUTION == scheduling_event_type:
            workflow_execution_id = context[EventContextConstant.WORKFLOW_EXECUTION_ID]
            task_name = context[EventContextConstant.TASK_NAME]
            current_task_execution_meta = self.metadata_manager.get_latest_task_execution(
                workflow_execution_id=workflow_execution_id,
                task_name=task_name)
            if current_task_execution_meta is None \
                    or TaskStatus(current_task_execution_meta.status) not in TASK_ALIVE_SET:
                task_execution_meta = self.metadata_manager.add_task_execution(
                    workflow_execution_id=workflow_execution_id,
                    task_name=task_name)
                new_task_execution = TaskExecutionKey(workflow_execution_id=workflow_execution_id,
                                                      task_name=task_name,
                                                      seq_num=task_execution_meta.sequence_number)
                return WorkflowExecutionScheduleCommand(
                    workflow_execution_id=workflow_execution_id,
                    task_schedule_commands=[TaskScheduleCommand(action=TaskAction.START,
                                                                new_task_execution=new_task_execution)])
            else:
                logging.info("Ignore the start task execution event({}), because the task({}) is alive."
                             .format(event, task_name))
        elif SchedulingEventType.RESTART_TASK_EXECUTION == scheduling_event_type:
            return self.restart_task_execution(context)
        elif SchedulingEventType.STOP_TASK_EXECUTION == scheduling_event_type:
            task_execution_id = context[EventContextConstant.TASK_EXECUTION_ID]
            task_execution = self.metadata_manager.get_task_execution(task_execution_id=task_execution_id)
            return WorkflowExecutionScheduleCommand(
                workflow_execution_id=task_execution.workflow_execution_id,
                task_schedule_commands=[TaskScheduleCommand(
                    action=TaskAction.STOP,
                    current_task_execution=TaskExecutionKey(workflow_execution_id=task_execution.workflow_execution_id,
                                                            task_name=task_execution.task_name,
                                                            seq_num=task_execution.sequence_number))])
        elif SchedulingEventType.PERIODIC_RUN_WORKFLOW == scheduling_event_type:
            schedule_id = context[EventContextConstant.WORKFLOW_SCHEDULE_ID]
            workflow_schedule = self.metadata_manager.get_workflow_schedule(schedule_id=schedule_id)
            snapshot = self.metadata_manager.get_latest_snapshot(workflow_id=workflow_schedule.workflow_id)
            return WorkflowExecutionStartCommand(snapshot_id=snapshot.id,
                                                 run_type=ExecutionType.PERIODIC)
        elif SchedulingEventType.PERIODIC_RUN_TASK == scheduling_event_type:
            return self.restart_task_execution(context)
        else:
            logging.warning("Ignore the scheduling event: {}.".format(str(event)))

    def restart_task_execution(self, context):
        workflow_execution_id = context[EventContextConstant.WORKFLOW_EXECUTION_ID]
        task_name = context[EventContextConstant.TASK_NAME]
        task_execution = self.metadata_manager.get_latest_task_execution(
            workflow_execution_id=workflow_execution_id,
            task_name=task_name)
        task_execution_meta = self.metadata_manager.add_task_execution(
            workflow_execution_id=workflow_execution_id,
            task_name=task_name)
        if task_execution is None:
            current_task_execution = None
        else:
            current_task_execution = TaskExecutionKey(
                workflow_execution_id=task_execution.workflow_execution_id,
                task_name=task_execution.task_name,
                seq_num=task_execution.sequence_number
            )
        return WorkflowExecutionScheduleCommand(
            workflow_execution_id=workflow_execution_id,
            task_schedule_commands=[TaskScheduleCommand(
                action=TaskAction.RESTART,
                current_task_execution=current_task_execution,
                new_task_execution=TaskExecutionKey(workflow_execution_id=workflow_execution_id,
                                                    task_name=task_name,
                                                    seq_num=task_execution_meta.sequence_number))])