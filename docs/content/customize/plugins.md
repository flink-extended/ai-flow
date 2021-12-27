# Plugins

While AIFlow works well out of the box, sometimes users may want to integrate AIFlow with their existing environment more closely. For example, an organization may want AIFlow to submit Flink jobs to their internal Flink platform instead of submitting the jobs to YARN or Kubernetes directly. AIFlow plugins is designed to cater to such cases.

At this point, AIFlow supports the following plugins.

- **job_plugin**: AIFlow has provided the support for a few commonly used jobs, including shell script, Python script and Apache Flink jobs. However, more likely than not, users may want to add new job types. For example, the jobs are submitted to the internal platform, or some other job engines like TensorFlow or Spark are used. In such cases, one may find the job_plugins handy.
- **blob_manager_plugin**: AIFlow assumes that there is a storage to upload the workflow code and dependencies for the workflow executions. The support for local file system and Alibaba OSS is provided out of the box. Users can implement a blob_manager_plugin to integrate AIFlow with other storage systems.
- **scheduler_plugin**: By default, AIFlow uses a modified version of Apache AirFlow which supports event-based scheduling. Although we are not aware of other event-based schedulers at the moment, if users do want to try another scheduler, they can implement a *scheduler_plugin* and let AIFlow use that. 

We encourage users and developers to share their plugin implementations with each other so people don't have to implement the same plugins repeatedly.

## Job Plugin

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
2. The __init__.py of your Python module should register the `JobPluginFactory` by doing something like following:

```
from ai_flow.plugin_interface import register_job_plugin_factory
from ai_flow_plugins.job_plugins.python.python_job_plugin import PythonJobPluginFactory
# Expose public APIs for the Python job plugin.
from ai_flow_plugins.job_plugins.python.python_processor import PythonProcessor
from ai_flow_plugins.job_plugins.python.python_job_config import PythonJobConfig

# Register the PythonJobPlugin to AIFlow.
register_job_plugin_factory(PythonJobPluginFactory())
```

### Define a job using the job plugin

After a job plugin is registered, users can specify the job_type in the corresponding job configuration to let AIFlow know which job plugin should be used to run the job. For example, to define the job with job name "foo" as a Python job, one can put the following configurations in the workflow configuration yaml file.

```
    ...
    [job_name]:
        job_type: python
    ...
```

## Blob Manager Plugin

When executing a workflow, AIFlow will upload the corresponding artifacts(code, dependencies and resources) to a shared storage. AIFlow does that for two purposes:

1. Make the distribution of the artifacts easier and more scalable in a distributed environment.
2. Take a snapshot of the code for each execution, so that users can easily see what is the workflow that is running even after something is changed.

AIFlow relies on a blob manager to upload and download the artifacts. The blob manager is a pluggable component and currently AIFlow provides implementations based on local file system and Alibaba OSS out of the box.

### Implement a blob manager plugin

To create a blob manager plugin, one needs to implement a subclass of ``ai_flow.plugin_interface.blob_manager_interface.BlobManager`` to upload and download artifacts. To take configurations upon construction, the subclass should have a `__init__(self, config: Dict)` method. The configurations can be added when one setup AIFlow to use the custom blob manager (see next section).

The [OssBlobManager](https://github.com/flink-extended/ai-flow/tree/master/ai_flow_plugins/blob_manager_plugins/oss_blob_manager.py) is a good example for the other implementations.

### Use a custom blob manager

To use a custom blob manager, users can set the ``blob.blob_manager_class`` config in the project configuration yaml file to specify the blob manager class and additional configurations. For example, the following configuration snippet sets up the OSS Blob Manager,

```
    ...
    blob:
      blob_manager_class: ai_flow_plugins.blob_manager_plugins.oss_blob_manager.OssBlobManager
      blob_manager_config:
        access_key_id:
        access_key_secret:
        endpoint: 
        bucket: 
        root_directory:
    ...
```

## Scheduler Plugin Interface

By default, AIFlow server provides a modified version of AirFlow that supports event-based scheduling (EBS) to execute the workflows. Moreover, the scheduler also exposes the interface to manipulate the workflow and job executions. Although we are not aware of other schedulers capable of doing the same at this point, users can still create a custom scheduler for AIFlow if they want to.

### Implement a scheduler plugin

Compared with other plugins, implementation of the scheduler plugin might be a bit more involved. To create a scheduler plugin, one needs to implement a subclass of ``ai_flow.plugins_interface.scheduler_interface.Scheduler``. To take configurations upon construction, the subclass should have a `__init__(self, config: Dict)` method. The configurations for construction can be added to the AIFlow server configuration yaml file when one setup AIFlow server to use the custom scheduler. (see next section).

``ai_flow_plugins.scheduler_plugins.airflow_scheduler.AirFlowScheduler`` is a good example of the implementation of the scheduler plugin.

### Use a custom scheduler

To let AIFlow use a custom scheduler, one should set the ``scheduler.scheduler_class_name`` configuration in the server configuration yaml file, along with the configuration to construct the custom scheduler. The following example shows how to setup AIFlow server to use `AirFlowScheduler`.

```

    scheduler:
        scheduler_class_name: ai_flow_plugins.scheduler_plugins.airflow.airflow_scheduler.AirFlowScheduler
        scheduler_config:
            airflow_deploy_path: /root/airflow/dag
            notification_server_uri: localhost:50052

```
