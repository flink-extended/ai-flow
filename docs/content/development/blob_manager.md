# Blob Manager

AIFlow uses `blob manager` to share artifacts(code, dependencies, and resources) among hosts. The `blob manager` is central storage that supports uploading and downloading files. There are four purposes of having a `blob manager`.

* The AIFlow client needs to submit artifacts(code, dependencies, and resources) to AIFlow server.
* The AIFlow Server needs to distribute artifacts among workers.
* The artifacts of each execution should be stored in persistent storage.
* Users may need to transfer files between jobs in the same project.

The `blob manager` is a pluggable component and currently, AIFlow provides some commonly used implementations, you can choose one of them or even implement your own `BlobManager` if needed.

## Provided Blob Manager

### LocalBlobManager

`LocalBlobManager` is only used when the AIFlow client, server, and workers are all on the same host because it relies on the local file system. The way to use `LocalBlobManager` is to put the following configurations in `project.yaml`.

```yaml
blob:
  blob_manager_class: ai_flow_plugins.blob_manager_plugins.local_blob_manager.LocalBlobManager
  blob_manager_config:
    root_directory: [The directory of local filesystem to store artifacts]
```

### OssBlobManager

`OssBlobManager` relies on [Alibaba Cloud OSS](https://www.alibabacloud.com/en/product/object-storage-service) to store artifacts. To use `OssBlobManager` you need to install python SDK for OSS client on every node which needs to access `OssBlobManager`.

```shell
pip install 'ai-flow[oss]'
```

Then you can put the following configurations in `project.yaml` to enable `OssBlobManager`.

```yaml
blob:
  blob_manager_class: ai_flow_plugins.blob_manager_plugins.oss_blob_manager.OssBlobManager
  blob_manager_config:
        access_key_id: [The id of the access key]
        access_key_secret: [The secret of the access key]
        endpoint: [Access domain name or CNAME]
        bucket: [The name of the bucket]
        root_directory: [The logical directory of the bucket to store artifacts]
```

### HDFSBlobManager

`HDFSBlobManager` relies on HDFS to store artifacts. To use `HDFSBlobManager` you need to install python SDK for HDFS client on every node which needs to access `HDFSBlobManager`.

```shell
pip install 'ai-flow[hdfs]'
```

Then you can put the following configurations in `project.yaml` to enable `HDFSBlobManager`.

```yaml
blob:
  blob_manager_class: ai_flow_plugins.blob_manager_plugins.hdfs_blob_manager.HDFSBlobManager
  blob_manager_config:
        hdfs_url: [WebHDFS url]
        hdfs_user: [The user to access HDFS]
        root_directory: [The directory to store artifacts]
```

### S3BlobManager

`S3BlobManager` relies on Amazon S3 to store artifacts. To use `S3BlobManager` you need to install python SDK for S3 client on every node which needs to access `S3BlobManager`.

```shell
pip install 'ai-flow[s3]'
```

Then you can put the following configurations in `project.yaml` to enable `S3BlobManager`.

```yaml
blob:
  blob_manager_class: ai_flow_plugins.blob_manager_plugins.s3_blob_manager.S3BlobManager
  blob_manager_config:
        service_name: [The name of a service, e.g. 's3' or 'ec2']
        region_name: [The name of the region associated with the client]
        api_version: [The API version to use]
        use_ssl: [Whether or not to use SSL]
        verify: [Whether or not to verify SSL certificates]
        endpoint_url: [The complete URL to use for the constructed client]
        access_key_id: [The access key for your AWS account]
        secret_access_key: [The secret key for your AWS account]
        session_token: [The session key for your AWS account]
        config: [Advanced client configuration options]
        bucket_name: [The S3 bucket name]
```

## Using Blob Manager in Workflow

The `blob manager` is not only be used by the AIFlow framework, users can also upload or download files using configured `blob manager`, e.g.

```python
from ai_flow.context.project_context import current_project_config
from ai_flow.workflow.workflow import WorkflowPropertyKeys
from ai_flow.plugin_interface.blob_manager_interface import BlobConfig, BlobManagerFactory

blob_config = BlobConfig(current_project_config().get(WorkflowPropertyKeys.BLOB))
blob_manager = BlobManagerFactory.create_blob_manager(blob_config.blob_manager_class(),
                                                      blob_config.blob_manager_config())
blob_manager.upload(local_file_path='/tmp')
```

## Customized Blob Manager

You can also implement your own `blob manager` if the built-in ones do not meet your requirements. Please refer to [Blob Manager Plugin](../customize/blob_manager_plugin.md) for more information.
