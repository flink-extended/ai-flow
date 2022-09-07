# Workflow Executions

A [Workflow](./workflows.md) can be executed to generate runtime instances, which is called Workflow Execution. 

## Workflow Execution Status

A Workflow Execution has a Status representing what stage of the lifecycle it is in. The possible Status for a Workflow Execution is:

- init: The workflow execution is just created.
- running: One or more task of the workflow execution is running.
- success: All tasks of the workflow execution are successful.
- failed: Any of the tasks of the workflow execution is failed.
- stopped: The workflow execution is requested to shut down and successfully stopped


## Creating Workflow Execution

There are 3 ways to run Workflow and generate Workflow Executions.

## Manually

Users can manually start an execution of a Workflow immediately by the command-line interface.
```bash
aiflow workflow-execution start my_workflow
```
### Periodically 

A Workflow can be bound to a [Workflow Schedule](./workflow_schedules.md) to make it run periodically.

### Driven by Events

A Workflow can be bound to a [Workflow Trigger](./workflow_triggers.md) to make it can be triggered by Events and Conditions. 