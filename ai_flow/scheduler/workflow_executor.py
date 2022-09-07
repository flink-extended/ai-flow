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
from typing import Optional, Union

import cloudpickle

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.metadata.metadata_manager import MetadataManager, Filters, FilterIn
from ai_flow.model.action import TaskAction
from ai_flow.model.status import TASK_ALIVE_SET, WorkflowStatus
from ai_flow.model.task_execution import TaskExecutionKey
from ai_flow.model.workflow import Workflow
from ai_flow.scheduler.schedule_command import WorkflowExecutionStartCommand, TaskScheduleCommand, \
    WorkflowExecutionScheduleCommand, WorkflowExecutionStopCommand


class WorkflowExecutor(object):
    """WorkflowExecutor execute start a workflow command or stop a workflow execution command."""
    def __init__(self, metadata_manager: MetadataManager):
        self.metadata_manager = metadata_manager

    def execute(self, schedule_cmd: Union[WorkflowExecutionStartCommand, WorkflowExecutionStopCommand]) \
            -> Optional[WorkflowExecutionScheduleCommand]:
        """
        :param schedule_cmd: It is a starting workflow command or stopping workflow execution command.
        :return: A schedule workflow execution command.
        """
        if isinstance(schedule_cmd, WorkflowExecutionStartCommand):
            snapshot_meta = self.metadata_manager.get_workflow_snapshot(snapshot_id=schedule_cmd.snapshot_id)
            if not snapshot_meta:
                raise AIFlowException(f"Cannot find workflow snapshot with id: {schedule_cmd.snapshot_id}")
            workflow_execution_meta = self.metadata_manager.add_workflow_execution(workflow_id=snapshot_meta.workflow_id,
                                                                                   run_type=schedule_cmd.run_type.value,
                                                                                   snapshot_id=schedule_cmd.snapshot_id)
            self.metadata_manager.flush()
            snapshot_meta = self.metadata_manager.get_workflow_snapshot(snapshot_id=schedule_cmd.snapshot_id)
            workflow: Workflow = cloudpickle.loads(snapshot_meta.workflow_object)
            task_schedule_commands = []
            for task_name in workflow.tasks.keys():
                if task_name in workflow.rules:
                    able_to_start = True
                    for rule in workflow.rules.get(task_name):
                        if rule.action == TaskAction.START:
                            able_to_start = False
                    if not able_to_start:
                        continue
                task_execution_meta = self.metadata_manager.add_task_execution(
                    workflow_execution_id=workflow_execution_meta.id,
                    task_name=task_name)
                task_cmd = TaskScheduleCommand(action=TaskAction.START,
                                               new_task_execution=TaskExecutionKey(
                                                   workflow_execution_id=workflow_execution_meta.id,
                                                   task_name=task_name,
                                                   seq_num=task_execution_meta.sequence_number,
                                               ))
                task_schedule_commands.append(task_cmd)
            self.metadata_manager.update_workflow_execution(workflow_execution_id=workflow_execution_meta.id,
                                                            status=WorkflowStatus.RUNNING.value)
            self.metadata_manager.flush()
            if len(task_schedule_commands) > 0:
                return WorkflowExecutionScheduleCommand(workflow_execution_id=workflow_execution_meta.id,
                                                        task_schedule_commands=task_schedule_commands)
            else:
                return None
        else:
            task_execution_metas = self.metadata_manager.list_task_executions(
                workflow_execution_id=schedule_cmd.workflow_execution_id,
                page_size=None,
                filters=Filters([(FilterIn('status'), list(TASK_ALIVE_SET))])
            )
            if task_execution_metas is not None:
                task_schedule_commands = []
                for task_execution in task_execution_metas:
                    task_cmd = TaskScheduleCommand(action=TaskAction.STOP,
                                                   current_task_execution=TaskExecutionKey(
                                                       workflow_execution_id=task_execution.workflow_execution_id,
                                                       task_name=task_execution.task_name,
                                                       seq_num=task_execution.sequence_number,
                                                   ))
                    task_schedule_commands.append(task_cmd)
                self.metadata_manager.update_workflow_execution(
                    workflow_execution_id=schedule_cmd.workflow_execution_id,
                    status=WorkflowStatus.STOPPED.value
                )
                self.metadata_manager.flush()
                if len(task_schedule_commands) > 0:
                    return WorkflowExecutionScheduleCommand(workflow_execution_id=schedule_cmd.workflow_execution_id,
                                                            task_schedule_commands=task_schedule_commands)
                else:
                    return None
            else:
                return None
