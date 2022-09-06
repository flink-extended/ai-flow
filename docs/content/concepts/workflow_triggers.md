# Workflow Triggers

Similar to [Task Rule](./task_rules.md), a Workflow can also have some rules on it called **Workflow Trigger**, however, a Workflow Trigger only consists of Event and Condition. 
When the Event comes and the Condition is satisfied, the Workflow would be started, and no other types of Action(stop, restart) are supported.

## Creating Workflow Triggers

User can create a Workflow Trigger by `ops.add_workflow_trigger` with a `WorkflowRule` passed, e.g. the following code makes workflow `event_triggered_workflow` execute as long as received an event with key `trigger_workflow`.

```python
from ai_flow import ops
from ai_flow.model.internal.conditions import SingleEventCondition
from ai_flow.model.rule import WorkflowRule
from ai_flow.model.workflow import Workflow
from ai_flow.notification.notification_client import AIFlowNotificationClient
from ai_flow.operators.bash import BashOperator
from ai_flow.operators.python import PythonOperator

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

```text
Currently, only Python API is supported to create Workflow Trigger. 
```

## Viewing Triggers

Users can view all Workflow Triggers of the Workflow by the following command:
```shell script
aiflow workflow-trigger list workflow_name
```

## Pausing and Resuming Triggers

If you want to temporarily stop a Workflow Trigger, you can run the following command.
```shell script
aiflow workflow-trigger pause workflow_trigger_id
```
Note that the above command doesn’t delete the metadata of the Workflow Trigger, you can resume the trigger if needed.
```shell script
aiflow workflow-trigger resume workflow_trigger_id
```

## Deleting Triggers
To completely delete the metadata of the Workflow Trigger, you can use the `delete` sub-command.

```shell script
aiflow workflow-trigger delete workflow_trigger_id
```