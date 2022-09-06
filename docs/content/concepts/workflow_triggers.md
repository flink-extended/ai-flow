# Workflow Triggers

Similar to [Task Rule](./task_rules.md), a Workflow can also have some rules on it called **Workflow Trigger**, however, a Workflow Trigger only consists of Event and Condition. 
When the Event comes and the Condition is satisfied, the Workflow would be started, and no other types of Action(stop, restart) are supported.

## Writing Workflow Triggers

User can create a Workflow Trigger by `ops.add_workflow_trigger` with a `WorkflowRule` passed, e.g. the following code makes workflow `event_triggered_workflow` execute as long as received an event with key `trigger_workflow`.

```python
from ai_flow import ops

def send_event():
    client = AIFlowNotificationClient(server_uri='localhost:50052')
    client.send_event(key='trigger_workflow', value=None)


with Workflow(name='event_trigger_workflow_1') as w1:
    event_task = PythonOperator(name='event_task',
                                python_callable=send_event)

with Workflow(name='event_trigger_workflow_2') as w2:
    task1 = BashOperator(name='task1',
                         bash_command='echo I am 1st task.')


if __name__ == "__main__":
    ops.upload_workflows(__file__)
    trigger_rule = WorkflowRule(SingleEventCondition(expect_event_key="trigger_workflow"))
    ops.add_workflow_trigger(rule=trigger_rule, workflow_name='event_trigger_workflow_2')
    ops.start_workflow_execution('event_trigger_workflow_1')
```