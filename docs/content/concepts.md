# Concepts

## Workflow
A workflow consists of [tasks](#Tasks) and relationships between tasks. A workflow can run regularly or be triggered by [events](#Events).

## Namespaces
A namespace can contains multiple business related workflows. Workflows with the same names in different namespaces can be uniquely identified.

## Tasks
A Task is the basic unit of execution in workflow. Tasks are arranged into a workflow, and they have dependencies between them in order to express the conditions on which they should run.

## Operators
An Operator is conceptually a template for a predefined [task](#Tasks).

## Task Executions
A task execution is the runtime instance of a [task](#Tasks). A task can be executed for multiple times which generates multiple job executions.

## Workflow Executions
The workflow execution is a runtime instance of the [workflow](#Workflow).
A workflow can be executed multiple times to generate multiple workflow executions.

## Events
The event specifies the signal that triggers evaluating [condition](#Conditions) and taking the [task action](#Task Actions). 

## Conditions
Consists of the conditions that need to be satisfied in order to carry out the specified [task action](#Task Actions). The condition is only checked upon occurrence of the specified [event](#Events).

## Task Actions
A task can perform the following actions: 
* START: creates a new execution of the task
* STOP: stops the running execution of the task
* RESTART: stops the current running execution and starts a new task execution
