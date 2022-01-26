# Use the Blob

We currently also provide other implementations of `BlobManager` like `OssBlobManager` and `HDFSBlobManager` which allows users to **submit their workflow to a remote AIFlow Server**.

* `OssBlobManager`

```yaml
project_name: tutorial_project
server_uri: [Remote AIFlow server uri]
notification_server_uri: [Remote Notification server uri]
blob:
  blob_manager_class: ai_flow_plugins.blob_manager_plugins.oss_blob_manager.OssBlobManager
  blob_manager_config:
        access_key_id: [The id of the access key]
        access_key_secret: [The secret of the access key]
        endpoint: [Access domain name or CNAME]
        bucket: [The name of the bucket]
        root_directory: [The upload directory of the bucket]
```

* `HDFSBlobManager`

```yaml
project_name: tutorial_project
server_uri: [Remote AIFlow server uri]
notification_server_uri: [Remote Notification server uri]
blob:
  blob_manager_class: ai_flow_plugins.blob_manager_plugins.hdfs_blob_manager.HDFSBlobManager
  blob_manager_config:
        hdfs_url: [Hostname or IP address of HDFS namenode, prefixed with protocol, followed by WebHDFS port on namenode]
        hdfs_user: [User default. Defaults to the current user's (as determined by `whoami`)]
        root_directory: [The upload directory of the bucket]
```

* `S3BlobManager`

```yaml
project_name: tutorial_project
server_uri: [Remote AIFlow server uri]
notification_server_uri: [Remote Notification server uri]
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

