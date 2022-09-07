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
from ai_flow.metadata.workflow_execution import WorkflowExecutionMeta
from ai_flow.model.execution_type import ExecutionType
from ai_flow.model.status import WorkflowStatus
from ai_flow.model.workflow_execution import WorkflowExecution


def workflow_execution_meta_to_workflow_execution(workflow_execution_meta: WorkflowExecutionMeta) -> WorkflowExecution:
    return WorkflowExecution(workflow_id=workflow_execution_meta.workflow_id,
                             execution_type=ExecutionType(workflow_execution_meta.run_type),
                             begin_date=workflow_execution_meta.begin_date,
                             end_date=workflow_execution_meta.end_date,
                             status=WorkflowStatus(workflow_execution_meta.status),
                             id=workflow_execution_meta.id)