# Creating Workflows

## Preparing the Structure

All workflows of a project are organized in the `workflows` directory, the structure should be as follow:
```yaml
|- workflows/
    |- first_workflow/
         |- first_workflow.py
         |- first_workflow.yaml
    |- second_workflow/
         |- second_workflow.py
         |- second_workflow.yaml
```

A workflow is identified by a unique name, which is the name of the directory of workflow. For each workflow, it must contain a python file to define the logic of the workflow and a YAML file to configure the jobs.

```{note}
AIFlow uses the following convention to avoid redundant configurations, that is the names of the python files (e.g. first_workflow.py) and YAML files (e.g. first_workflow.yaml) must be same as the name of the parent directory(e.g. first_workflow).
```

## Defining the Workflow

We define [workflow](../concepts.md#workflow) in Python. The workflow can be described as a graph, [jobs](../concepts.md#Job) are represented as the nodes while the relationship between jobs are represented as the edge. 

### Initializing the Context

Before defining the workflow, you need to initialize the context of the workflow as below:

```python
import ai_flow as af

af.init_ai_flow_context()
```

### Defining Jobs

You can define a simple job like below in the python file:

```python
import ai_flow as af
from ai_flow_plugins.job_plugins.bash import BashProcessor

with af.job_config('job_1'):
    af.user_define_operation(processor=BashProcessor("sleep 5"))
```

### Defining the Relationship 

AIFlow mainly supports two functions to define the relationship between jobs.

- action_on_job_status: this function is used to set the behavior of downstream jobs when the status of upstream jobs changes.
- action_on_events: this function is used to set the behavior of a job when some events happened.

## Configuring the workflow

We set the properties of the workflow in a YAML file, includes the configurations of the workflow itself along with the configurations of jobs in the workflow.

### Configuring Jobs

You can configure the type, run interval, or other custom configuration of the job in the YAML file. AIFlow would use the job plugin corresponding to the job type you configured to execute the job. The simplest job config is as follow:

```yaml
job_1:
  job_type: bash
  periodic_config:
    cron: "0 * * * * * *"
```

### Configuring the Workflow

Except for job-related configurations, you can also do some configurations for the workflow. The workflow configuraions mainly includes two parts:

- periodic configuration
- custom properties

E.g.


```yaml
periodic_config:
  interval: "1,1,0,0"

properties:
  owner: Bob

```

### A Full Example

For more comprehensive understanding, you can follow the [tutorial](../get_started/tutorial.md) to write a complete workflow step by step.

