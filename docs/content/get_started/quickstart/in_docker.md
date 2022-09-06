# Running AIFlow in Docker

This section will show you how to start AIFlow in docker container if you are tired of managing the python environment and dependencies.

## Pulling Docker Image
Run following command to pull latest AIFlow docker image.
```shell script
docker pull flinkaiflow/flink-ai-flow:latest
```

## Running Docker Container
Run following command to enter the docker container in interactive mode.
```shell script
docker run -it -p 8080:8080 -p 8000:8000 flinkaiflow/flink-ai-flow:latest /bin/bash
```

## Starting AIFlow 

### Starting Notification Server
AIFlow depends on notification service as an event dispatcher. Before running AIFlow, you need to start notification server.
```shell script
# Initialize configuration
notification config init 

# Initialize database and tables
notification db init

# Start notification server as a daemon
notification server start -d &
``` 

### Starting AIFlow Server
```shell script
# Initialize configuration
aiflow config init

# Initialize database and tables
aiflow db init

# Start AIFlow server as a daemon
aiflow server start -d &
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

from ai_flow.rpc.client.aiflow_client import get_notification_client
from notification_service.model.event import EventKey, Event

from ai_flow.model.action import TaskAction
from ai_flow.operators.bash import BashOperator
from ai_flow.operators.python import PythonOperator
from ai_flow.model.status import TaskStatus

from ai_flow.model.workflow import Workflow

EVENT_KEY = EventKey(name='quickstart_key',
                     event_type='quickstart_type')


def func():
    time.sleep(5)
    notification_client = get_notification_client()
    event = Event(event_key=EVENT_KEY, message='This is a custom message.')
    notification_client.send_event(event)


with Workflow(name='quickstart_workflow') as w1:
    task1 = BashOperator(name='task1', bash_command='echo I am 1st task.')
    task2 = BashOperator(name='task2', bash_command='echo I am 2nd task.')
    task3 = PythonOperator(name='task3', python_callable=func)
    task4 = BashOperator(name='task4', bash_command='echo I am 4th task.')

    task3.action_on_task_status(TaskAction.START, {
        task1: TaskStatus.SUCCESS,
        task2: TaskStatus.SUCCESS
    })

    task4.action_on_event_received(action=TaskAction.RESTART, event_key=EVENT_KEY)
```
You can save the above workflow as a python file on your workstation and remember the file path as ${path_of_the_workflow_file}.

### Uploading the Workflow

Now you can upload the workflow with the path of the file you just saved.
```
aiflow workflow upload ${path_of_the_workflow_file}
```

You can view the workflow you uploaded by the following command.
```shell script
aiflow workflow list --namespace default
```

### Starting an Execution
The workflow you uploaded can be executed as an instance which is called execution. You can start a new execution by the following command.
```
aiflow workflow-execution start quickstart_workflow --namespace default
```

### Viewing the Results
You can view the workflow execution you just started by the following command.
```shell script
aiflow workflow-execution list quickstart_workflow --namespace default
```
The result shows `id`, `status` and other information of the workflow execution.
You can then list tasks of workflow execution with id 1 by the following command.
```shell script
aiflow task-execution list 1
```
Also you can check the log under `${AIFLOW_HOME}/aiflow/logs` to view the outputs of tasks.


## What’s Next?

For more details about how to write your own workflow, please refer to the [tutorial](../../tutorial_and_examples/tutorial.md) and  [development](../../development/index.md) document.
