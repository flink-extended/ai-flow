# Client Configurations

As a client-server application, AIFlow allows users to access the server from any network connected machine.
That means you can upload and manage the workflow from any client. An AIFlow client needs a configuration file `aiflow_client.yaml` under ${AIFLOW_HOME}.
Here are the configurations of the `aiflow_client.yaml`.

|Key|Type|Default|Description|
|---|---|---|---|
|server_address|String|localhost:50051|The uri of the AIFlow server.|
|blob_manager_class|String|ai_flow.blob_manager.impl.local_blob_manager.LocalBlobManager|The fully-qualified name of the `Blob Manager` class.|
|blob_manager_config|dict|None|Custom configuration of this type of implementation.|

For the full blob manager config, please refer to [here](../plugins/blob_manager_plugin.md)

## Default AIFlow server Configuration

```yaml
# address of AIFlow server
server_address: localhost:50051

# configurations about blob manager
blob_manager:
  blob_manager_class: ai_flow.blob_manager.impl.local_blob_manager.LocalBlobManager
  blob_manager_config:
    root_directory: {AIFLOW_HOME}/blob
```
