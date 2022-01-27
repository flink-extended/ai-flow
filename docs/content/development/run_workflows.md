# Running Workflows

## Submitting the Workflows
Before running the workflow, you need to submit the code and configuration of your workflow to remote AIFlowServer.
There are two ways to submit the workflow.

1. Command-Line Interface
    ```shell script
    aiflow workflow submit {project_path} {workflow_name}
    ```
2. Python API
    ```python
    import ai_flow as af
    
    af.init_ai_flow_context()
    
    workflow_name = af.current_workflow_config().workflow_name
    af.workflow_operation.submit_workflow(workflow_name)
    ```

## Running the Workflow
At this point you can manually start to run the workflow you just submitted. Every time you run the workflow, a new [workflow execution](./concepts.md#Workflow Execution) would be created. You also have 2 ways to start a new workflow execution.

1. Command-Line Interface
    ```shell script
   # project_path is the root directory of the project contains the workflow
   # workflow_name is the unique name of the workflow 
   
   aiflow workflow start-execution {project_path} {workflow_name}
   ```
2. Python API
    ```python
    import ai_flow as af
    
    af.init_ai_flow_context()
    
    workflow_name = af.current_workflow_config().workflow_name
    af.workflow_operation.start_new_workflow_execution(workflow_name)
    ```