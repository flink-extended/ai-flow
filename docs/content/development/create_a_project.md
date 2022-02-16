# Creating A Project

Some workflows may be business-related, they have the same client configuration and shared dependencies. AIFlow recommend users to put these workflows into a [project](../concepts.md#Project). 

Workflows in the same project are organized in the same directory of the project along with common config files and shared dependencies. 

## Project Structure

Users need to prepare a separate directory to organize workflows and related resource files. The structure of the directory should be as follows:

```
root_directory/
    |- workflows/
       |- first_workflow/
          |- first_workflow.py 
          |- first_workflow.yaml 
    |- dependencies/
        |-python/
        |-jar/
    |- resources/
    └─ project.yaml
```

`root_directory` is the root directory of the project, it can be renamed it as needed.

The `workflows` directory is used to save codes and config files of workflows in this project. For more information about organizing workflows, please refer to [create workflows](create_workflows.md).

The `dependencies` directory is used to save python/jar dependencies that will be used by workflows. The dependencies would be packaged and uploaded to workers that execute the workflow.

The `resources` directory is for saving all other user files(e.g., config files) that will be used by the project. It would also be uploaded to workers that execute the workflow.

The `project.yaml` is the config file of the project, we will describe the details in the following section.

## Config project

Each project has a file named `project.yaml` to takes configurations the project. The config file has following configuration keys or  sections:

* project_name: the project's name, which will be the default `namespace` of workflows in this project as well. 
* server_uri: the URI that the AIFlow Server is running on, so that the workflows in project can communicate with.
* notification_server_uri: the URI that the Notification Server is running on, so that the workflows in project can communicate with.
* blob: this section specifies where the project codes would be uploaded so that the AIFlow Server and workers could download the codes to execute. For more details about configuring blob, please refer to [Blob Manager Plugin](../plugins/blob_manager_plugin.md).

A complete example of `project.yaml`.

```yaml
project_name: aiflow-examples
server_uri: localhost:50051
notification_server_uri: localhost:50052
blob:
  blob_manager_class: ai_flow_plugins.blob_manager_plugins.local_blob_manager.LocalBlobManager
  blob_manager_config:
    root_directory: /tmp/aiflow-examples/demo
```

Here we choose `LocalBlobManager` and as the blob manager, so the AIFlow Server will download the workflow code locally. More types of blob manager, please refer to [Blob Manager Plugin](../plugins/blob_manager_plugin.md). 