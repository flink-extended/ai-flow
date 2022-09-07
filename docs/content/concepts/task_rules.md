# Task Rules

A Task/Operator usually has some rules which describe when and how it should take action. A Task Rule consists of three parts:
* [Event](./events.md) - it specifies the signal that triggers the invocation of the rule
* [Condition](./conditions.md) - it is a logical test that, if satisfied or evaluates to be true, causes the action to be carried out
* Action - START, STOP or RESTART the task

In a Workflow, those Tasks that do not have rules that Action is `START` will be executed as long as the Workflow starts. 
During the execution of those Tasks that run first, some Events would be generated to trigger the other Tasks to run.

Next, we will go deep into some types of Rules to help thoroughly understand them.

## Status Rules

The most common Task Rule is that one task runs after the other tasks succeed, users can add such Rules by calling `start_after` API.

```python
from ai_flow.model.workflow import Workflow
from ai_flow.operators.bash import BashOperator

with Workflow(name='my_workflow') as workflow:
    task1 = BashOperator(name='task_1',
                         bash_command='echo I am the 1st task')
    task2 = BashOperator(name='task_2',
                         bash_command='echo I am the 2nd task')
    task2.start_after([task1, ])
```
`task1` has no Rules that Action is `START` so it would execute first, and `task2` will start running after `task1` succeed.

More generally, a task may perform other actions after more than one task is finished with any status, users can add such Rules by calling `action_on_task_status` API.
```python
from ai_flow.model.action import TaskAction
from ai_flow.model.status import TaskStatus
from ai_flow.model.workflow import Workflow
from ai_flow.operators.bash import BashOperator

with Workflow(name='my_workflow') as workflow:  
    task1 = BashOperator(name='task_1',
                         bash_command='sleep 10')
    task2 = BashOperator(name='task_2',
                         bash_command='sleep 20')
    task3 = BashOperator(name='task_3',
                         bash_command='sleep 100')
    task3.action_on_task_status(action=TaskAction.STOP,
                                upstream_task_status_dict={
                                    task1: TaskStatus.SUCCESS,
                                    task2: TaskStatus.SUCCESS
                                })
```
Since all 3 tasks have no Rules that Action is `START` so they will execute once the workflow starts, but `task3` won't finish after 100 seconds, instead it will be stopped when both `task1` and `task2` succeed.

## Single Event Rules

Another commonly used Task Rule is that one task takes actions after receiving an event, users can add such Rules by calling `action_on_event_received` API.
```python
import time

from ai_flow.model.action import TaskAction
from ai_flow.model.workflow import Workflow
from ai_flow.notification.notification_client import AIFlowNotificationClient
from ai_flow.operators.bash import BashOperator
from ai_flow.operators.python import PythonOperator

def func():  
    time.sleep(5)
    print('I am the 1st task')
    notification_client = AIFlowNotificationClient("localhost:50052")
    notification_client.send_event(key="key",
                                   value="")

with Workflow(name='quickstart_workflow') as workflow:
    task1 = PythonOperator(name='task1', python_callable=func)
    task2 = BashOperator(name='task2', bash_command='echo I am the 2nd task.')
    task2.action_on_event_received(action=TaskAction.START, event_key="key")
```
`task1` would send a custom event that triggers `task2` to start running.

## Custom Rules

Sometimes users may want to take action on tasks only when they receive multiple events or satisfy more complex conditions. 
In those scenarios, users can add custom Task Rules by calling `action_on_condition` API, e.g. in the below example, `task1` sends an event with a number and `task2` would be triggered when the number adds up to 100.
```python
import random
import time

from notification_service.model.event import Event

from ai_flow.model.action import TaskAction
from ai_flow.model.condition import Condition
from ai_flow.model.context import Context
from ai_flow.model.state import ValueState, ValueStateDescriptor
from ai_flow.model.workflow import Workflow
from ai_flow.notification.notification_client import AIFlowNotificationClient
from ai_flow.operators.bash import BashOperator
from ai_flow.operators.python import PythonOperator

class NumCondition(Condition):
    def is_met(self, event: Event, context: Context) -> bool:
        state: ValueState = context.get_state(ValueStateDescriptor(name='num_state'))
        num = 0 if state.value() is None else int(state.value())
        num += int(event.value)
        if num >= 100:
            return True
        else:
            state.update(num)
            return False

def random_produce():
    notification_client = \
        AIFlowNotificationClient(server_uri='localhost:50052')
    while True:
        num = random.randint(0, 9)
        notification_client.send_event(key='num_event', value=str(num))
        time.sleep(1)

with Workflow(name='condition_workflow') as workflow:
    task1 = PythonOperator(name='producer',
                           python_callable=random_produce)
    task2 = BashOperator(name='consumer',
                         bash_command='echo Got 100 records.')

    task2.action_on_condition(action=TaskAction.START,
                              condition=NumCondition(expect_event_keys=['num_event']))
```