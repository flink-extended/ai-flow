#
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
from ai_flow import ops
from ai_flow.model.action import TaskAction
from ai_flow.model.status import TaskStatus
from ai_flow.operators.bash import BashOperator
from ai_flow.model.workflow import Workflow

"""
Tasks of workflow can run periodically by passing `periodic_expression` as parameter.
The expression format is the same as the expression of WorkflowSchedule.
"""

with Workflow(name='periodic_task_example') as workflow:
    task1 = BashOperator(name='task_1',
                         bash_command='echo I am the 1st task',
                         periodic_expression='cron@*/1 * * * *')
    task2 = BashOperator(name='task_2',
                         bash_command='echo I am the 2nd task')
    task2.start_after([task1, ])

    task3 = BashOperator(name='task_3',
                         bash_command='echo I am the 3rd task',
                         periodic_expression='interval@0 0 1 0')
    task4 = BashOperator(name='task_4',
                         bash_command='echo I am the 4th task')
    task4.start_after([task3, ])


if __name__ == "__main__":
    ops.upload_workflows(__file__)
    ops.start_workflow_execution("periodic_task_example")
