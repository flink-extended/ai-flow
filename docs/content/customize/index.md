# Customize
While AIFlow works well out of the box, sometimes users may want to integrate AIFlow with their existing environment more closely. For example, an organization may want AIFlow to submit Flink jobs to their internal Flink platform instead of submitting the jobs to YARN or Kubernetes directly. AIFlow plugins is designed to cater to such cases.

At this point, AIFlow supports the following plugins.

- **job_plugin**: AIFlow has provided the support for a few commonly used jobs, including shell script, Python script and Apache Flink jobs. However, more likely than not, users may want to add new job types. For example, the jobs are submitted to the internal platform, or some other job engines like TensorFlow or Spark are used. In such cases, one may find the job_plugins handy.
- **blob_manager_plugin**: AIFlow assumes that there is a storage to upload the workflow code and dependencies for the workflow executions. The support for local file system and Alibaba OSS is provided out of the box. Users can implement a blob_manager_plugin to integrate AIFlow with other storage systems.
- **scheduler_plugin**: By default, AIFlow uses a modified version of Apache AirFlow which supports event-based scheduling. Although we are not aware of other event-based schedulers at the moment, if users do want to try another scheduler, they can implement a *scheduler_plugin* and let AIFlow use that. 

We encourage users and developers to share their plugin implementations with each other so people don't have to implement the same plugins repeatedly.

```{toctree}
:maxdepth: 1

job_plugin
notification_server
scheduler
```