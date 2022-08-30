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
from ai_flow.model.internal.conditions import SingleEventCondition
from ai_flow.model.rule import WorkflowRule
from ai_flow.model.workflow import Workflow
from ai_flow.notification.notification_client import AIFlowNotificationClient
from ai_flow.operators.bash import BashOperator
from ai_flow.operators.python import PythonOperator


def send_event():
    print("Sending event...")
    client = AIFlowNotificationClient(server_uri='localhost:50052')
    client.send_event(key='trigger_workflow', value=None)


with Workflow(name='event_trigger_workflow_1', namespace='sample') as w1:
    event_task = PythonOperator(name='event_task',
                                python_callable=send_event)

with Workflow(name='event_trigger_workflow_2', namespace='sample') as w2:
    task1 = BashOperator(name='task1', bash_command='echo I am 1st task.')


if __name__ == "__main__":
    ops.upload_workflows(__file__)
    trigger_rule = WorkflowRule(SingleEventCondition(expect_event="trigger_workflow"))
    ops.add_workflow_trigger(rule=trigger_rule, workflow_name='event_triggered_workflow')
    ops.start_workflow_execution('event_workflow')
