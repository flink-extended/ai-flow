# Blob Manager Plugin

When executing a workflow, AIFlow will upload the corresponding artifacts(code, dependencies and resources) to a shared storage. AIFlow does that for two purposes:

1. Make the distribution of the artifacts easier and more scalable in a distributed environment.
2. Take a snapshot of the code for each execution, so that users can easily see what is the workflow that is running even after something is changed.

AIFlow relies on a blob manager to upload and download the artifacts. The blob manager is a pluggable component and currently AIFlow provides implementations based on local file system and Alibaba OSS out of the box.

## Implement a blob manager plugin

To create a blob manager plugin, one needs to implement a subclass of ``ai_flow.plugin_interface.blob_manager_interface.BlobManager`` to upload and download artifacts. To take configurations upon construction, the subclass should have a `__init__(self, config: Dict)` method. The configurations can be added when one setup AIFlow to use the custom blob manager (see next section).

The [OssBlobManager](https://github.com/flink-extended/ai-flow/tree/master/ai_flow_plugins/blob_manager_plugins/oss_blob_manager.py) is a good example for the other implementations.

## Use a custom blob manager

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