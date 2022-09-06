# Workflows

A Workflow consists of [Tasks](#Tasks), organized with [Task Rules](./rules.md) to describe how they should run. 
The Workflow and Tasks are defined in a Python script which just acts as a configuration file specifying the Workflow’s structure as code.

## Declaring Workflows

A Workflow is declared in a `with` statement, which includes all Tasks and Task Rules inside it.

```python
with Workflow(name='my_workflow') as workflow:
    task1 = BashOperator(name='task_1',
                         bash_command='echo I am the 1st task')
    task2 = BashOperator(name='task_2',
                         bash_command='echo I am the 2nd task')
    task2.start_after([task1, ])
```
AIFlow will execute the Python file and then load any Workflow objects at the _top level_ in the file. This means you can define multiple Workflows per Python file.

## Uploading Workflows

Users can upload Workflows by the command-line interface. In addition to the Python file containing the Workflow objects, other files that are used in Workflow definition and execution should also be uploaded by `--files` option.
```bash
aiflow workflow upload workflow.py --files f1,f2
```

## Running Workflows
A Workflow can be executed to generate runtime instances, which is called _workflow execution_. There are 3 ways to run Workflow and generate _workflow executions_.

### Manually

Users can manually start an execution of a Workflow immediately by the command-line interface.
```bash
aiflow workflow-execution start my_workflow
```
### Periodically 

A Workflow can be bound to a [Workflow Schedule](./schedule.md) to make it run periodically.

### Driven by Events

A Workflow can be bound to a [Workflow Trigger](./trigger.md) to make it can be triggered by Events and Conditions. 

## Workflow disabling and deletion

A Workflow can be disabled which means no more Workflow Executions or Task Executions will be scheduled.
```bash
aiflow workflow disable workflow_name
```
However, the disabling operation does not delete the metadata of the Workflow, users can enable the Workflow to resume the scheduling of it if needed.
```bash
aiflow workflow enable workflow_name
```
If you want to not only disable the workflow but also delete the metadata, please run the following command:
```bash
aiflow workflow delete workflow name
```
```{note}  
The deletion command truncates all metadata of the Workflow in cascade, including Workflows, Workflow Executions and Task Executions, so before deleting the Workflow, please make sure that no executions of the Workflow is still running.
```