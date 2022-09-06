# Tasks

A Task is the basic unit of execution in [Workflow](./workflows.md). Tasks are arranged into a Workflow, and they have [Task Rules](./task_rules.md) between them in order to describe the conditions under which they should run.


## Task Executions
Much in the same way that a [Workflow](./workflows.md) is instantiated into a Workflow Execution each time it runs, the tasks are instantiated into _Task Executions_. 

A Task Execution has a Status representing what stage of the lifecycle it is in. The possible Status for a Task Execution is:

- init: The task execution has not yet been queued (its dependencies are not yet met)
- queued: The task execution has been assigned to an Executor and is awaiting a worker
- running: The task execution is running on a worker
- success: The task execution finished running without errors
- failed: The task execution had an error during execution and failed to run
- stopping: The task execution was externally requested to shut down when it was running, but not yet finish stopping
- stopped: The task execution is requested to shut down and successfully stopped
- retrying: The task execution failed, but has retry attempts left and will be rescheduled.

```{note}
In a Workflow Execution, there can be only one running execution of each task.
```

## Task Actions
A Task can perform different actions according to the [Task Rule](./task_rules.md). There are three kinds of actions of a task.

- start: Start a new Task Execution if there is no running execution, otherwise do nothing.
- stop: Stop a running Task Execution.
- restart: Stop the currently running Task Execution and start a new execution.
