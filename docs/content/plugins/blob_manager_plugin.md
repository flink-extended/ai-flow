# Blob Manager Plugin

`Blob Managers` are the central storage that supports uploading and downloading files. There are four purposes of having them:

* The AIFlow client needs to submit artifacts(user codes, dependencies, and resources) to AIFlow server.
* The AIFlow Server needs to distribute artifacts among workers.
* The artifacts of each execution should be stored in persistent storage for restoring.
* Users may need to transfer files between jobs in the same project.

`Blob Managers` have a common API and are “pluggable”, meaning you can swap `Blob Manager` based on your needs. AIFlow provides some built-in implementations, you can choose one of them or even implement your own `BlobManager` if needed. 

Each project can only have one `Blob Manager` configured at a time, this is set by the `blob` section on top-level of the `project.yaml`.   The `blob` section has two required sub-configs:

- blob_manager_class: the fully-qualified name of the `Blob Manager` class.
- blob_manager_config: custom configuration of this type of implementation.

## Built-in Blob Managers

### LocalBlobManager

`LocalBlobManager` is only used when the AIFlow client, server, and workers are all on the same host because it relies on the local file system. `LocalBlobManager` has following custom configurations:

| Key            | Type   | DESCRIPTION                                               |
| -------------- | ------ | --------------------------------------------------------- |
| root_directory | String | The root directory of local filesystem to store artifacts |


A complete configuration example of `LocalBlobManager` in `project.yaml`.

```yaml
blob:
  blob_manager_class: ai_flow_plugins.blob_manager_plugins.local_blob_manager.LocalBlobManager
  blob_manager_config:
    root_directory: /tmp
```

### OssBlobManager

`OssBlobManager` relies on [Alibaba Cloud OSS](https://www.alibabacloud.com/en/product/object-storage-service) to store resources. To use `OssBlobManager` you need to install python SDK for OSS client on every node that needs to access OSS file system.

```shell
pip install 'ai-flow[oss]'
```

 `OssBlobManager` has following custom configurations:

| Key               | Type   | DESCRIPTION                                        |
| ----------------- | ------ | -------------------------------------------------- |
| root_directory    | String | The root path of OSS filesystem to store artifacts |
| access_key_id     | String | The id of the access key                           |
| access_key_secret | String | The secret of the access key                       |
| endpoint          | String | Access domain name or CNAME                        |
| bucket            | String | The name of OSS bucket                             |


A complete configuration example of `OssBlobManager` in `project.yaml`.

```yaml
blob:
  blob_manager_class: ai_flow_plugins.blob_manager_plugins.oss_blob_manager.OssBlobManager
  blob_manager_config:
        access_key_id: xxx
        access_key_secret: xxx
        endpoint: oss-cn-hangzhou.aliyuncs.com
        bucket: ai-flow
        root_directory: tmp
```

### HDFSBlobManager

`HDFSBlobManager` relies on HDFS to store resources. To use `HDFSBlobManager` you need to install python SDK for HDFS client on every node which needs to access `HDFSBlobManager`.

```shell
pip install 'ai-flow[hdfs]'
```

 `HDFSBlobManager` has following custom configurations:

| Key            | Type   | DESCRIPTION                                         |
| -------------- | ------ | --------------------------------------------------- |
| hdfs_url       | String | The url of WebHDFS                                  |
| hdfs_user      | String | The user to access HDFS                             |
| root_directory | String | The root path of HDFS filesystem to store artifacts |


A complete configuration example of `HDFSBlobManager` in `project.yaml`.

```yaml
blob:
  blob_manager_class: ai_flow_plugins.blob_manager_plugins.hdfs_blob_manager.HDFSBlobManager
  blob_manager_config:
    hdfs_url: http://hadoop-dfs:50070
    hdfs_user: hdfs
    root_directory: /tmp
```

### S3BlobManager

// TODO

## Using Blob Manager in a Workflow

The `Blob Manager` is not only be used by the AIFlow framework, users can also upload or download files with the `Blob Manager` if it has been configured in `project.yaml`.  E.g.

```python
from ai_flow.context.project_context import current_project_config
from ai_flow.workflow.workflow import WorkflowPropertyKeys
from ai_flow.plugin_interface.blob_manager_interface import BlobConfig, BlobManagerFactory

blob_config = BlobConfig(current_project_config().get(WorkflowPropertyKeys.BLOB))
blob_manager = BlobManagerFactory.create_blob_manager(blob_config.blob_manager_class(),
                                                      blob_config.blob_manager_config())
blob_manager.upload(local_file_path='/tmp/file')
```

## Customizing Blob Manager

You can also implement your own `Blob Manager` if the built-in ones do not meet your requirements. To create a blob manager plugin, one needs to implement a subclass of ``ai_flow.plugin_interface.blob_manager_interface.BlobManager`` to upload and download artifacts. To take configurations upon construction, the subclass should have a `__init__(self, config: Dict)` method. The configurations can be added when someone setup AIFlow to use the custom blob manager.

