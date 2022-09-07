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
from ai_flow.model.action import TaskAction
from ai_flow.operators.bash import BashOperator
from ai_flow.model.status import TaskStatus

from ai_flow.model.workflow import Workflow

with Workflow(name='workflow1') as w1:
    task1 = BashOperator(name='task1', bash_command='echo hello')
    task2 = BashOperator(name='task2', bash_command='sleep 10')
    task3 = BashOperator(name='task3', bash_command='echo hello3')
    task3.action_on_task_status(TaskAction.START, {
        task1: TaskStatus.SUCCESS,
        task2: TaskStatus.SUCCESS
    })

with Workflow(name='workflow2') as w2:
    task1 = BashOperator(name='task1', bash_command='echo hello')
    task2 = BashOperator(name='task2', bash_command='sleep 10')
    task3 = BashOperator(name='task3', bash_command='echo hello3')
    task3.action_on_task_status(TaskAction.START, {
        task1: TaskStatus.SUCCESS,
        task2: TaskStatus.SUCCESS
    })
