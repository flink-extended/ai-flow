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
from datetime import datetime

from ai_flow.model.execution_type import ExecutionType
from ai_flow.model.status import TaskStatus


class TaskExecution(object):
    """
    TaskExecution describes an instance of a task. It can be created by the scheduler.
    """
    def __init__(self,
                 workflow_execution_id: int,
                 task_name: str,
                 sequence_number: int,
                 try_number: int,
                 execution_type: ExecutionType,
                 begin_date: datetime,
                 end_date: datetime,
                 status: TaskStatus,
                 id: int = None
                 ):
        """
        :param workflow_execution_id: TaskExecution belongs to the unique identifier of WorkflowExecution.
        :param task_name: The name of the task it belongs to.
        :param sequence_number: A task in a WorkflowExecution can be run multiple times,
                                it indicates how many times this task is run.
        :param try_number: TaskExecution will retry if it fails to run, try_number represents the total number of runs.
        :param execution_type: The type that triggers TaskExecution.
        :param begin_date: The time TaskExecution started executing.
        :param end_date: The time TaskExecution ends execution.
        :param status: TaskExecution's current status.
        :param id: Unique ID of TaskExecution.
        """
        self.id = id
        self.workflow_execution_id = workflow_execution_id
        self.task_name = task_name
        self.sequence_number = sequence_number
        self.try_number = try_number
        self.execution_type = execution_type
        self.begin_date = begin_date
        self.end_date = end_date
        self.status = status

