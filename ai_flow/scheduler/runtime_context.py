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
from ai_flow.metadata.metadata_manager import MetadataManager
from ai_flow.model.internal.contexts import WorkflowContext, WorkflowExecutionContext, TaskExecutionContext
from ai_flow.model.state import State, StateDescriptor
from ai_flow.model.status import TaskStatus
from ai_flow.model.task_execution import TaskExecution, TaskExecutionKey
from ai_flow.model.workflow import Workflow
from ai_flow.model.workflow_execution import WorkflowExecution


class WorkflowContextImpl(WorkflowContext):

    def __init__(self,
                 namespace: str,
                 workflow: Workflow,
                 metadata_manager: MetadataManager):
        super().__init__(namespace, workflow)
        self._metadata_manager = metadata_manager

    def get_state(self, state_descriptor: StateDescriptor) -> State:
        workflow_meta = self._metadata_manager.get_workflow_by_name(namespace=self.namespace, name=self.workflow.name)
        return self._metadata_manager.get_or_create_workflow_state(
            workflow_id=workflow_meta.id,
            descriptor=state_descriptor)


class WorkflowExecutionContextImpl(WorkflowExecutionContext):
    def __init__(self,
                 workflow: Workflow,
                 workflow_execution: WorkflowExecution,
                 metadata_manager: MetadataManager):
        super().__init__(workflow, workflow_execution)
        self._metadata_manager = metadata_manager

    def get_state(self, state_descriptor: StateDescriptor) -> State:
        return self._metadata_manager.get_or_create_workflow_execution_state(
            workflow_execution_id=self.workflow_execution.id,
            descriptor=state_descriptor)

    def get_task_status(self, task_name) -> TaskStatus:
        task_execution = self._metadata_manager.get_latest_task_execution(
            self.workflow_execution.id, task_name)
        if task_execution is not None:
            return TaskStatus(task_execution.status)
        else:
            return None


class TaskExecutionContextImpl(TaskExecutionContext):
    def __init__(self,
                 workflow: Workflow,
                 task_execution_key: TaskExecutionKey,
                 metadata_manager: MetadataManager):
        super().__init__(workflow, task_execution_key)
        self._metadata_manager = metadata_manager

    def get_state(self, state_descriptor: StateDescriptor) -> State:
        return self._metadata_manager.get_or_create_workflow_execution_state(
            workflow_execution_id=self.task_execution_key.workflow_execution_id,
            descriptor=state_descriptor)
