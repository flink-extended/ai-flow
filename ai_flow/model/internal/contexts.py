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
from ai_flow.model.context import Context
from ai_flow.model.task_execution import TaskExecution
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
                 workflow_execution: WorkflowExecution,
                 task_execution: TaskExecution):
        self.workflow = workflow
        self.workflow_execution = workflow_execution
        self.task_execution = task_execution
