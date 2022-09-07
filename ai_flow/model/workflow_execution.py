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
from datetime import datetime

from ai_flow.model.execution_type import ExecutionType
from ai_flow.model.status import WorkflowStatus


class WorkflowExecution(object):
    """
    WorkflowExecution describes an instance of a Workflow. It can be created by the scheduler.
    """
    def __init__(self,
                 workflow_id,
                 execution_type: ExecutionType,
                 begin_date: datetime,
                 end_date: datetime,
                 status: WorkflowStatus,
                 id: int = None
                 ):
        """
        :param workflow_id: WorkflowExecution belongs to the unique identifier of Workflow.
        :param execution_type: The type that triggers WorkflowExecution.
        :param begin_date: The time WorkflowExecution started executing.
        :param end_date: The time WorkflowExecution ends execution.
        :param status: WorkflowExecution's current status.
        :param id: Unique ID of WorkflowExecution.
        """
        self.workflow_id = workflow_id
        self.execution_type = execution_type
        self.begin_date = begin_date
        self.end_date = end_date
        self.status = status
        self.id = id
