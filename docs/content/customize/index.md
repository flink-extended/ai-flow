# Customize
While AIFlow works well out of the box, sometimes users may want to integrate AIFlow with their existing environment more closely. For example, an organization may want AIFlow to submit Flink jobs to their internal Flink platform instead of submitting the jobs to YARN or Kubernetes directly. AIFlow plugins is designed to cater to such cases.

At this point, AIFlow supports the following plugins.

- job_plugin
- blob_manager_plugin
- scheduler_plugin

We encourage users and developers to share their plugin implementations with each other so people don't have to implement the same plugins repeatedly.

```{toctree}
:maxdepth: 1

job_plugin
blob_manager_plugin
scheduler_plugin
```