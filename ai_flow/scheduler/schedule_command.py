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
from typing import List

from ai_flow.model.action import TaskAction
from ai_flow.model.execution_type import ExecutionType
from ai_flow.model.task_execution import TaskExecutionKey


class TaskScheduleCommand(object):
    """The command to schedule tasks"""

    def __init__(self,
                 action: TaskAction,
                 current_task_execution: TaskExecutionKey = None,
                 new_task_execution: TaskExecutionKey = None):
        """
        :param action: The type of command to schedule the task.
        :param current_task_execution: The current task execution.
        :param new_task_execution: Need to create a new task execution.
        """
        self.action = action
        self.current_task_execution = current_task_execution
        self.new_task_execution = new_task_execution


class WorkflowExecutionScheduleCommand(object):
    """The command to schedule workflow executions"""

    def __init__(self, workflow_execution_id: int, task_schedule_commands: List[TaskScheduleCommand]):
        """
        :param workflow_execution_id: The identify of the workflow execution.
        :param task_schedule_commands: The commands of scheduling tasks in the workflow execution.
        """
        self.workflow_execution_id = workflow_execution_id
        self.task_schedule_commands = task_schedule_commands


class WorkflowScheduleCommand(object):
    """The command to schedule workflows"""

    def __init__(self, workflow_id: int, snapshot_id: int, run_type: ExecutionType = ExecutionType.EVENT):
        """
        :param workflow_id: The identify of the workflow.
        :param snapshot_id: The identity of the workflow snapshot.
        :param run_type: The run type of the workflow execution.
        """
        self.workflow_id = workflow_id
        self.snapshot_id = snapshot_id
        self.run_type = run_type
