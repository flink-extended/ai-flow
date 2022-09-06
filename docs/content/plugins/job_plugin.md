 Job Plugin
## Built-in Job Plugins

### Bash Job Plugin

`Bash Job Plugin` is used to define the job that will execute a bash command on worker. Users can define the job by creating a `BashProcessor` with bash command as parameter. Here is an [example](https://github.com/flink-extended/ai-flow/tree/master/examples/demo/workflows/bash) that helps understand.

### Python Job Plugin

`Python Job Plugin` is used to define and execute the job that is described in Python. Unlike `BashProcessor`, AIFlow allows users to write their own Python processor by implementing basic class `PythonProcessor`. Here is an [example](https://github.com/flink-extended/ai-flow/tree/master/examples/demo/workflows/python) that helps understand.

### Flink Job Plugin

`Flink Job Plugin` is used to define and submit the [Flink](https://flink.apache.org/) job.  Due to Flink supporting different types of API, AIFlow also provides the following processors to adapt.

* FlinkJavaProcessor
* FlinkPythonProcessor
* FlinkSqlProcessor

Here is an [example](https://github.com/flink-extended/ai-flow/tree/master/examples/demo/workflows/flink) that helps understand.

## Using Job Plugin in a Job

Users can specify the job_type in the corresponding job configuration to let AIFlow know which job plugin should be used to run the job. For example, to define the job with job name "job_1" as a Python job, one can put the following configurations in the workflow configuration yaml file.

```yaml
job_1:
  job_type: python
```

## Customizing Job Manager

AIFlow has provided the support for a few commonly used jobs, including shell script, Python script and Apache Flink jobs. However, more likely than not, users may want to add new job types. For example, the jobs are submitted to the internal platform, or some other job engines like TensorFlow or Spark are used. In such cases, one may find the job_plugins handy.

### Implement a job plugin

Before we explain how to implement a job plugin, it is helpful to understand how AIFlow takes the user processing logic, compiles them into executable jobs and schedules the jobs to run.

As explained in the [Overview](../architecture/overview.md), users of AIFlow describe each job in a `with` block which defines the job name and corresponding `JobConfig`. Inside each `with` block, users can define the logic of the job by connecting several `AINode` with `DataEdge`, where each `AINode` has a processor hosting the processing logic. All the connected `AINode`s within the `with` block compose an `AISubGraph`. Therefore, each `Job` in AIFlow is associated with a `JobConfig` and an `AISubGraph`.

In order to run the `AISubGraph`, AIFlow relies on `JobGenerator`s to translate the `AISubGraph` to an executable `Job` format which can then be submitted and run by a corresponding `JobController`.

With that, in order to create a job plugin one will need to implement the following classes:

1. A subclass of ``ai_flow.workflow.job.Job`` to encapsulates the necessary information to run the job, e.g. the configurations of the job, how to translate the `AISubGraph`, how to submit the job, etc.
2. A subclass of ``ai_flow.translator.translator.JobGenerator`` to translates an `AISubGraph` to a `Job` defined in 1.
3. A subclass of ``ai_flow.plugins_interface.job_plugin_interface.JobController`` to manipulate the `Job` generated in 2.
4. A subclass of ``ai_flow.plugins_interface.job_plugin_interface.JobPluginFactory`` to let AIFlow discover and use the plugin.

The implementation of Python job plugin and Flink job plugin might be good examples for new implementations.

In the implementation for Python engine, [PythonJobGenerator](https://github.com/flink-extended/ai-flow/tree/master/ai_flow_plugins/job_plugins/python/python_job_plugin.py#L61) generates the Python modules described by [PythonJob](https://github.com/flink-extended/ai-flow/tree/master/ai_flow_plugins/job_plugins/python/python_job_plugin.py#L41).
The [PythonJobController](https://github.com/flink-extended/ai-flow/tree/master/ai_flow_plugins/job_plugins/python/python_job_plugin.py#L85) controls the Python job submission which returns the [PythonJobHandle](https://github.com/flink-extended/ai-flow/tree/master/ai_flow_plugins/job_plugins/python/python_job_plugin.py#L52) which again can be passed to the PythonJobController to stop and clean the corresponding Python job.

### Register a job plugin

The job plugins can only be used after they are registered. To register a job plugin, make sure that:

1. Your plugins are put into Python modules and are in the Python path of both the client and the server.
2. The `__init__.py` of your job plugin Python module should register the `JobPluginFactory` by doing something like following:

```
from ai_flow.plugin_interface import register_job_plugin_factory
from ai_flow_plugins.job_plugins.python.python_job_plugin import PythonJobPluginFactory
# Expose public APIs for the Python job plugin.
from ai_flow_plugins.job_plugins.python.python_processor import PythonProcessor
from ai_flow_plugins.job_plugins.python.python_job_config import PythonJobConfig

# Register the PythonJobPlugin to AIFlow.
register_job_plugin_factory(PythonJobPluginFactory())
```
