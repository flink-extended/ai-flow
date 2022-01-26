# Prepare Projects

A project contains multiple business related workflows. Before creating the workflow, we should prepare a project whose directory structure is as follows:

```
tutorial_project/
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

`tutorial_project` is the root directory of the project and `workflows` is used to save codes and config files of workflows in this project. 

The `dependecies` directory is used to save python/jar dependencies that will be used by our workflow.

The `resources` directory is for saving all other files(e.g., config files) that will be used by the project.

The `project.yaml` is the project config file. 

#### project.yaml

Every project has a project.yaml to takes some common configurations of all workflows in the project. Here is an example of the project.yaml for tutorial project.

```yaml
project_name: tutorial_project
server_uri: localhost:50051
notification_server_uri: localhost:50052
blob:
  blob_manager_class: ai_flow_plugins.blob_manager_plugins.local_blob_manager.LocalBlobManager
```

The `project_name` is used to define the project's name, which will be the default `namespace` of workflows in this project as well. 

```{note}
Namespace in AIFlow is used for isolation of events. Each workflow can only send events to its own namespace while it can listen on multiple namespaces. 
The reason for being able to listening on multiple namespaces is that the workflow could be triggered by external events.
```

The `server_uri` is where the AIFlow Server is running on, so that the workflows in project can communicate with .

For `notification_server_uri`,  they tell where the Notification Server is running on.

Then, we configure the `blob` property which specifies where the workflow code will be updated when submitting. 
It also tells the AIFlow Server where and how to download the workflow code.

Here we choose to use `LocalBlobManager` and as a result, the AIFlow Server will download the workflow code locally. 
Please note that `LocalBlobManager` can only work when you submit your workflow on the same machine as the AIFlow server. More types of blob manager, please refer to [Use the Blob](./use_the_blob.md). 
