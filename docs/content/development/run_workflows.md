# Running Workflows

AIFlow provides rich command-line interfaces to manage workflows, e.g., submit workflow to AIFlow Server, manually start a workflow execution, stop a workflow execution, etc.

## Submitting the Workflows

A workflow can be periodically scheduled or manually triggered, but before that, you need to submit the code and configuration of the workflow to remote AIFlow server. You could submit workflow by following command:

```shell script
# project_path is the root directory of the project contains the workflow
# workflow_name is the unique name of the workflow 

aiflow workflow submit {project_path} {workflow_name}
```

After that, you can view your workflow on web UI. If your workflow is periodic, you could find a new workflow execution is started automatically at the appointed time.

## Running the Workflow

At this point you can manually start to run the workflow you just submitted. Every time you run the workflow, a new [workflow execution](./concepts.md#Workflow Execution) would be created. 

```shell script
# project_path is the root directory of the project contains the workflow
# workflow_name is the unique name of the workflow 

aiflow workflow start-execution {project_path} {workflow_name}
```

For more operations about workflow, you can run `aiflow workflow --help` for details.