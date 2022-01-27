# Preparing Projects

A project contains multiple business-related projects workflows. These workflows are organized in the same directory of the project along with some common config files and resources.

## Preparing the Structure

Currently, users need to prepare the structure of the directory manually like follows:

```
aiflow-examples/
    |- workflows/
       |- first_workflow/
          |- first_workflow.py 
          |- first_workflow.yaml 
    |- dependencies/
        |-python 
        |-jar
    |- resources/
    └─ project.yaml
```

`aiflow-examples` is the root directory of the project, you can rename it as needed.

The `workflows` directory is used to save codes and config files of workflows in this project. For more information about organizing workflows, please refer to [create workflows](create_workflows.md).

The `dependencies` directory is used to save python/jar dependencies that will be used by your workflows. The dependencies would be packaged and uploaded to workers that execute the workflow.

The `resources` directory is for saving all other user files(e.g., config files) that will be used by the project. It would also be uploaded to workers that execute the workflow.

The `project.yaml` is the config file of the project, we will describe the details in the following section.

## Project Config

Every project has a `project.yaml` to takes some common configurations of all workflows in the project. Here is an example of the project.yaml.

```yaml
project_name: aiflow-examples
server_uri: localhost:50051
notification_server_uri: localhost:50052
blob:
  blob_manager_class: ai_flow_plugins.blob_manager_plugins.local_blob_manager.LocalBlobManager
  blob_manager_config:
    root_directory: /tmp/aiflow-examples/demo
```

The `project_name` is used to define the project's name, which will be the default `namespace` of workflows in this project as well. 

```{note}
Namespace in AIFlow is used for isolation of events. Each workflow can only send events to its own namespace while it can listen on multiple namespaces. 
The reason for being able to listening on multiple namespaces is that the workflow could be triggered by external events.
```

The `server_uri` is where the AIFlow Server is running on, so that the workflows in project can communicate with .

The `notification_server_uri` is where the Notification Server is running on, so that the workflows in project can communicate with.

The `blob` configuration block specifies where the project codes would be uploaded so that the AIFlow Server and workers could download the codes to execute. Here we choose to use `LocalBlobManager` and as a result, the AIFlow Server will download the workflow code locally. Please note that `LocalBlobManager` can only work when you submit your workflow on the same machine as the AIFlow server. More types of blob manager, please refer to [Blob Manager](./blob_manager.md). 
