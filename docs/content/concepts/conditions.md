# Conditions

A Condition is a logical test that, if satisfied or evaluates to be true, causes the action to be carried out. 

## When to evaluate

A Condition consists of a list of expected keys of [Events](./events.md) and a logical test, only when one of the expected [Events](./events.md) comes, the logical test will be evaluated.

## Custom Condition

It is allowed to define custom Conditions according to various scenarios by inheriting class `Condition` and implementing `is_met` function, e.g.
```python
from notification_service.model.event import Event

from ai_flow.model.condition import Condition
from ai_flow.model.context import Context
from ai_flow.model.state import ValueState, ValueStateDescriptor

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
```
The above examples shows a Condition that is satisfied only when it receives enough events that the number adds up to 100. With the `NumCondition`, we can easily define a Workflow that the consumer task starts only when the upstream producers prepared more than 100 records.
```python
import random
import time

from ai_flow.model.action import TaskAction
from ai_flow.model.workflow import Workflow
from ai_flow.notification.notification_client import AIFlowNotificationClient
from ai_flow.operators.bash import BashOperator
from ai_flow.operators.python import PythonOperator

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