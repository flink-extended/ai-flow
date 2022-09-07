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
import contextlib
import json

from ai_flow.model.context import Context
from ai_flow.model.task_execution import TaskExecutionKey
from ai_flow.model.workflow import Workflow
from ai_flow.model.workflow_execution import WorkflowExecution


class WorkflowContext(Context):
    """It contains a workflow information. It is used to execute workflow rules."""

    def __init__(self,
                 namespace: str,
                 workflow: Workflow):
        self.namespace = namespace
        self.workflow = workflow


class WorkflowExecutionContext(Context):
    """It contains a workflow and a workflow execution. It is used to execute task rules."""
    def __init__(self,
                 workflow: Workflow,
                 workflow_execution: WorkflowExecution):
        self.workflow = workflow
        self.workflow_execution = workflow_execution


class TaskExecutionContext(Context):
    """It contains a workflow, a workflow execution and a task execution. It is used to execute operators"""
    def __init__(self,
                 workflow: Workflow,
                 task_execution_key: TaskExecutionKey):
        self.workflow = workflow
        self.task_execution_key = task_execution_key


_CURRENT_TASK_CONTEXT: TaskExecutionContext = None


def set_runtime_task_context(context: TaskExecutionContext):
    global _CURRENT_TASK_CONTEXT
    _CURRENT_TASK_CONTEXT = context


def get_runtime_task_context() -> TaskExecutionContext:
    return _CURRENT_TASK_CONTEXT

