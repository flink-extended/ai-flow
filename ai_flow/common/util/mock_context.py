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
#
from ai_flow.model.task_execution import TaskExecutionKey

from ai_flow.model.workflow import Workflow

from ai_flow.model.internal.contexts import set_runtime_task_context, TaskExecutionContext


def set_mock_runtime_context():
    """
    This func is only for local task testing and debugging. Set a fake runtime context
    to avoid `AIFlowNotificationClient can only be used in AIFlow operators` exception.
    """
    mock_workflow = Workflow(name='mock_workflow')
    task_execution_key = TaskExecutionKey(1, 'mock_task', 1)
    context = TaskExecutionContext(workflow=mock_workflow,
                                   task_execution_key=task_execution_key)
    set_runtime_task_context(context)
