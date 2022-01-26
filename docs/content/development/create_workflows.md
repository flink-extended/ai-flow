# Create Workflows

## Prepare the Structure
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

## Define the Workflow
We define the logic of the workflow in a python file.

In our design, the workflow in AIFlow is a [AIGraph](https://github.com/flink-extended/ai-flow/blob/master/ai_flow/ai_graph/ai_graph.py#L28). Each node in the graph is an [AINode](https://github.com/flink-extended/ai-flow/blob/master/ai_flow/ai_graph/ai_node.py#L29), which contains a processor. Users should write their custom logic in the processor. 

In the AIGraph, nodes are connected by 2 types of edges, `DataEdge` means the destination node depends on the output of the source node, while `ControlEdge` means the destination node depends on the control conditions from source node. We will dive deeper into this kind of edges later.

### Define Jobs

For now, let's concentrate on the set of AINodes connected by only data edges. Such a set of nodes and data edges between them constitutes a sub-graph. This sub-graph, together with the predefined job config in workflow config yaml, is mapped to a Job by AIFlow framework. So, to summarize, each AIFlow job is made up of a job config, some AINodes and the data edges between those nodes. 

You can define a job like below in the python file:

```python
import ai_flow as af
from ai_flow_plugins.job_plugins.bash import BashProcessor

with af.job_config('job_1'):
    af.user_define_operation(processor=BashProcessor("sleep 5"))
```

### Define the Relationship 

AIFlow mainly supports two functions to define the relationship between jobs.

- action_on_job_status: this function is used to set the behavior of downstream jobs when the status of upstream jobs changes.
- action_on_events: this function is used to set the behavior of a job when some events happened.

## Configure the workflow

We set the properties of the workflow in a YAML file, includes the configurations of the workflow itself along with the configurations of jobs in the workflow.

### Configure Jobs

You can configure the type, run interval, or other custom configuration of the job in the YAML file. AIFlow would use the job plugin corresponding to the job type you configured to execute the job. The simplest job config is as follow:

```yaml
job_1:
  job_type: bash
```

### Configure the Workflow

Except for job-related configurations, you can also do some configurations for the workflow. The workflow configuraions mainly includes three parts:

- dependencies
- periodic configuration
- custom properties

E.g.


```yaml
periodic_config:
  start_date: "2020,1,1,1,1,1,"
  interval: "1,1,0,0"

properties:
  owner: Bob

dependencies:
  jars:
    - hadoop.jar
    - flink.jar
```

### An Example

Here's an tutorial example for you to 

