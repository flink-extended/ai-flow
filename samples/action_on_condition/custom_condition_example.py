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
import random
import time

from notification_service.model.event import Event, EventKey

from ai_flow.model.action import TaskAction
from ai_flow.model.condition import Condition
from ai_flow.model.context import Context
from ai_flow.model.state import ValueState, ValueStateDescriptor
from ai_flow.model.status import TaskStatus
from ai_flow.model.workflow import Workflow
from ai_flow.notification.notification_client import AIFlowNotificationClient
from ai_flow.operators.bash import BashOperator
from ai_flow.operators.python import PythonOperator

"""
This sample shows how to use custom conditions to orchestrate workflow. 

Consider we have 3 producer tasks keep producing records, these records will be 
consumed by the downstream consumer task. To save resources, the consumer task starts 
as long as there are 100 records get ready.
"""


class Consumer:
    def __init__(self,
                 is_consumed: bool = False,
                 accumulator: int = 0):
        self.is_consumed = is_consumed
        self.accumulator = accumulator


class NumCondition(Condition):

    def is_met(self, event: Event, context: Context) -> bool:
        state: ValueState = context.get_state(ValueStateDescriptor(name='consumer'))
        con = state.value()
        if con is None:
            con = Consumer()

        con.accumulator = con.accumulator + int(event.message)
        if con.accumulator >= 100 and not con.is_consumed:
            con.is_consumed = True
            state.update(con)
            return True
        else:
            state.update(con)
            return False


def random_produce():
    notification_client = AIFlowNotificationClient(
        server_uri='localhost:50052',
        namespace='sample',
        sender='record_producer',
    )
    while True:
        num = random.randint(0, 9)
        event: Event = Event(
            event_key=EventKey(name='name', event_type='NUM_GENERATED'),
            message=str(num)
        )
        notification_client.send_event(event)
        print(f"Produced {num} records")
        time.sleep(1)


with Workflow(name='condition_workflow') as workflow:
    task1 = PythonOperator(name='producer_1',
                           python_callable=random_produce)
    task2 = PythonOperator(name='producer_2',
                           python_callable=random_produce)
    task3 = PythonOperator(name='producer_3',
                           python_callable=random_produce)
    task4 = BashOperator(name='consumer',
                         bash_command='echo Got 100 records.')

    expected_event_key = EventKey(
        name='name',
        event_type='NUM_GENERATED',
        namespace='sample',
        sender='record_producer'
    )
    task4.action_on_condition(action=TaskAction.START,
                              condition=NumCondition(expect_events=[expected_event_key]))

    task1.action_on_task_status(action=TaskAction.STOP,
                                upstream_task_status_dict={task4: TaskStatus.SUCCESS})
    task2.action_on_task_status(action=TaskAction.STOP,
                                upstream_task_status_dict={task4: TaskStatus.SUCCESS})
    task3.action_on_task_status(action=TaskAction.STOP,
                                upstream_task_status_dict={task4: TaskStatus.SUCCESS})
