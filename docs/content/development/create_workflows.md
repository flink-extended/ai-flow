# Creating Workflows

Each workflow requires at least a Python file to define the workflow and a YAML configuration file. These files will be compiled to an executable workflow at client-side and submitted to AIFlow server to execute.

## Defining the Workflow

The workflow that defined in Python can be described as a graph, [jobs](../concepts.md#Job) are represented as the nodes while the [dependencies](../concepts.md) between jobs are represented as the edges. Users can follow below steps to define their own workflows.

### Initializing the Context

Before defining the workflow, you need to initialize the context and configuraion of the workflow as below:

```python
import ai_flow as af

af.init_ai_flow_context()
```

### Defining Jobs

A [job](../concepts.md#Job) may contains multiple processors but these operations must not have [control dependencies](../concepts.md#Control Dependency) among them. These processors should be defined in a single `with` statement.  For example,

```python
import ai_flow as af
from ai_flow_plugins.job_plugins.bash import BashProcessor

with af.job_config('job_1'):
    af.user_define_operation(processor=BashProcessor("sleep 5"))
```

The `user_define_operation` is the basic operation to construct an AINode, which takes a user-defined `processor`. The `processor` is defined in every implementation of [Job Plugins](../plugins/job_plugin.md). In addition to `user_define_operation`, there are also some convenient functions like `train`, `transform`, and `predict` to help with machine learning workflow definition. Users can find all APIs about workflow definition in [ops.py](https://github.com/flink-extended/ai-flow/blob/master/ai_flow/api/ops.py).

### Defining the Dependencies

The dependencies here is only [control dependency](../concepts.md#Control Dependency) which define the relationships between jobs. AIFlow mainly provides two functions to define the dependencies between jobs.

- action_on_job_status: this function is used to set the behavior of downstream jobs when the status of upstream jobs changes.
- action_on_events: this function is used to set the behavior of a job when some events happened. The events could be sent from other jobs in the same workflow or external process.

## Configuring the workflow

Workflow definition need to work with a configuration file. We set the properties of the workflow in a YAML file, includes the configurations of the workflow itself along with the configurations of jobs in the workflow.

### Configuring Jobs

You can configure the type, run interval, or other custom configuration of the job in the YAML file. AIFlow would use the job plugin corresponding to the job type you configured to execute the job. The simplest job config is as follow:

```yaml
job_1:
  job_type: bash
  periodic_config:
    cron: "0 * * * * * *"
```

### Configuring the Workflow

Except for job-related configurations, you can also do some configurations for the workflow. The workflow configuraions mainly includes periodic configuration or other custom properties. For example,


```yaml
periodic_config:
  interval: "1,1,0,0"

properties:
  owner: Bob
```

## A Full Example

For more comprehensive understanding, you can follow the [tutorial](../tutorial_and_examples/tutorial.md) to write a complete workflow step by step.

