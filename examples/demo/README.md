# Background
We provide some examples for using AIFlow, including event-triggered workflow scheduling, 
event-triggered job scheduling, periodic workflow scheduling, periodic job scheduling, etc.

# Check the Environment
Before running examples, check the AIFlow environment according 
to [quickstart](../../docs/content/get_started/quickstart.md).

# Submit a Workflow
You can submit a workflow with the command:
```shell
aiflow workflow submit ${project_path} ${workflow_name}
```

# Run a Workflow
You can run a workflow with the command:
```shell
aiflow workflow start-execution ${project_path} ${workflow_name}
```

# Index of Examples

[bash](workflows/bash)

[python](workflows/python)

[flink](workflows/flink)

[periodic_workflow_interval](workflows/periodic_workflow_interval)

[periodic_workflow_interval](workflows/periodic_workflow_cron)

[periodic_job](workflows/periodic_job)

[job_scheduling_on_status](workflows/job_scheduling_on_status)

[job_scheduling_on_events](workflows/job_scheduling_on_events)

[model_training](workflows/model_training)

[read_only_job](workflows/read_only_job)

[workflow_scheduling_on_events](workflows/workflow_scheduling_on_events)
