# Running AIFlow locally

This section will show you how to install and start AIFlow on your local workstation.

## Installing AIFlow
Please make sure that you have installed AIFlow refer to [installation guide](../../installation/index.md).


## Starting AIFlow 
### Starting Notification Server
AIFlow depends on notification service as an event dispatcher. Before running AIFlow, you need to start notification server.
```shell script
# Notification service needs a home directory. `~/notification_service` is the default, 
# but you can put it somewhere else if you prefer.
export NOTIFICATION_HOME=~/notification_service

# Initialize configuration
notification config init 

# Initialize database and tables
notification db init

# Start notification server as a daemon
notification server start -d
``` 

### Starting AIFlow Server
```shell script
# AIFlow needs a home directory. `~/aiflow` is the default, 
# but you can put it somewhere else if you prefer.
export AIFLOW_HOME=~/aiflow

# Initialize configuration
aiflow config init

# Initialize database and tables
aiflow db init

# Start AIFlow server as a daemon
aiflow server start -d
```

```{note}
You may run into issues caused by different operating systems or versions, 
please refer to [Troubleshooting](./troubleshooting.md) section to get solutions.
```

## Running a Workflow

### Defining a Workflow
Below is a typically event-driven workflow. The workflow contains 4 tasks, task3 is started once both task1 and task2 finished, then task3 will send a custom event which would trigger task4 to start running.

```python
import time

from ai_flow.model.action import TaskAction
from ai_flow.notification.notification_client import AIFlowNotificationClient
from ai_flow.operators.bash import BashOperator
from ai_flow.operators.python import PythonOperator
from ai_flow.model.workflow import Workflow

EVENT_KEY = "key"


def func():
    time.sleep(5)
    notification_client = AIFlowNotificationClient("localhost:50052")
    notification_client.send_event(key=EVENT_KEY,
                                   value='This is a custom message.')


with Workflow(name='quickstart_workflow') as w1:
    task1 = BashOperator(name='task1', bash_command='echo I am the 1st task.')
    task2 = BashOperator(name='task2', bash_command='echo I am the 2nd task.')
    task3 = PythonOperator(name='task3', python_callable=func)
    task4 = BashOperator(name='task4', bash_command='echo I am the 4th task.')

    task3.start_after([task1, task2])

    task4.action_on_event_received(action=TaskAction.START, event_key=EVENT_KEY)
```
You can save the above workflow as a python file on your workstation and remember the file path as ${path_of_the_workflow_file}.

### Uploading the Workflow

Now you can upload the workflow with the path of the file you just saved.
```
aiflow workflow upload ${path_of_the_workflow_file}
```

You can view the workflow you uploaded by the following command:
```shell script
aiflow workflow list --namespace default
```

### Starting an Execution
The workflow you uploaded can be executed as an instance which is called execution. You can start a new execution by the following command:
```
aiflow workflow-execution start quickstart_workflow --namespace default
```

### Viewing the Results
You can view the workflow execution you just started by the following command:
```shell script
aiflow workflow-execution list quickstart_workflow --namespace default
```
The result shows `id`, `status` and other information of the workflow execution.
You can then list tasks of workflow execution with id 1 by the following command:
```shell script
aiflow task-execution list 1
```
Also you can check the log under `${HOME}/aiflow/logs` to view the outputs of tasks.

## Stopping AIFlow 
### Stopping AIFlow Server
```shell script
# Stop AIFlow server, it may take a few seconds to wait for the server stopped.
aiflow server stop
```

### Stopping Notification Server
```shell script
# Stop Notification server
notification server stop
```

## What’s Next?

For more details about how to write your own workflow, please refer to the [tutorial](../../tutorial_and_examples/tutorial.md) and [concepts](../../concepts/index.md) document.
