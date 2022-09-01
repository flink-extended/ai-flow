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
from ai_flow.operators.bash import BashOperator
from ai_flow.model.workflow import Workflow

"""
A workflow can run periodically by binding a schedule to it.
The following 2 simple workflows are both bound to a schedule so they would be executed every 1 minute.
"""

with Workflow(name='periodic_workflow_by_cron') as w1:
    task = BashOperator(name='task', bash_command='echo Hello World!')


with Workflow(name='periodic_workflow_by_interval') as w2:
    task = BashOperator(name='task', bash_command='echo Hello World!')


if __name__ == "__main__":
    ops.upload_workflows(__file__)
    if not ops.list_workflow_schedules("periodic_workflow_by_cron"):
        ops.add_workflow_schedule(expression="cron@*/1 * * * *",
                                  workflow_name="periodic_workflow_by_cron")
    if not ops.list_workflow_schedules("periodic_workflow_by_interval"):
        ops.add_workflow_schedule(expression="interval@0 0 1 0",
                                  workflow_name="periodic_workflow_by_interval")
