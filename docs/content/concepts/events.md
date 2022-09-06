# Events
The event specifies the signal that triggers evaluating [Condition](./conditions.md) and taking the action. 
AIFlow scheduler relies on internal events to decide which Workflow and Tasks to perform actions. 
Users can also send custom Events in Tasks, there are three main uses of custom Events:

* Trigger a [Workflow Trigger](./workflow_triggers.md).
* Trigger a [Task Rule](./task_rules.md).
* Transfer messages between Tasks in the same namespace.

## Sending Events

A user Event is sent with `AIFlowNotificationClient`, and passing `key` and `value` with string type as parameters.
There are some design constraints to be aware of:
* The `AIFlowNotificationClient` can only be instantiated in a Task runtime.
* The Event can only be transferred in the same AIFlow [Namespace](./namespaces.md).
* If the Event is used to trigger [Task Rules](./task_rules.md), it can only effect on Tasks in the same Workflow Execution.

Here's an example of Tasks triggered by a custom Event.

```python

from ai_flow.model.action import TaskAction
from ai_flow.notification.notification_client import AIFlowNotificationClient
from ai_flow.operators.bash import BashOperator
from ai_flow.operators.python import PythonOperator

from ai_flow.model.workflow import Workflow

def func():
    notification_client = AIFlowNotificationClient("localhost:50052")  
    notification_client.send_event(key="key",
                                   value='This is a custom message.')  
  
with Workflow(name='workflow') as workflow:
    task1 = PythonOperator(name='task1', python_callable=func)
    task2 = BashOperator(name='task2', bash_command='echo I am the 2nd task.')
    
    task2.action_on_event_received(action=TaskAction.START, event_key="key")
```
## Listening Events

Users can also listen to Events with `AIFlowNotificationClient` in Tasks to receive messages from other Tasks. To listen to Events, you need to implement your own `ListenerProcessor` to define the logic of handling Events, e.g.

```python
from typing import List

from ai_flow.notification.notification_client import ListenerProcessor, Event


class Counter(ListenerProcessor):
    def __init__(self):
        self.counter = 0
    
    def process(self, events: List[Event]):
        self.counter += len(events)
```
Then you can start listening to Events by calling `register_listener`, e.g.
```python
from ai_flow.notification.notification_client import AIFlowNotificationClient

counter = Counter()
client = AIFlowNotificationClient("localhost:50052")
listener_id = client.register_listener(listener_processor=counter,
                                       event_keys=['expect_key',])
```
`register_listener` will create a new thread to listen to Events with key=`expect_key`, so please remember to call `unregister_listener` to release resources.
```python
client.unregister_listener(listener_id)
```