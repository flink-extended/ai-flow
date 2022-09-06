# AIFlow

## Command Line Interface

AIFlow has a very rich command-line interface that supports many types of operations on a Workflow, starting services and testing.

**Content**

* Positional Arguments
* Sub-commands:  

  * [config](aiflow-cli-config)
  * [db](aiflow-cli-db)
  * [namespace](aiflow-cli-namespace)
  * [server](aiflow-cli-server)
  * [workflow](aiflow-cli-workflow)
  * [workflow-execution](aiflow-cli-workflow-execution)
  * [task-execution](aiflow-cli-task-execution)
  * [workflow-schedule](aiflow-cli-workflow-schedule)
  * [workflow-trigger](aiflow-cli-workflow-trigger)
  * [webserver](aiflow-cli-webserver)
  * [version](aiflow-cli-version)

```
usage: aiflow [-h] COMMAND ... 
```

## Positional Arguments

> GROUP_OR_COMMAND

Possible choices: config, db, namespace, server, task-execution, workflow, workflow-execution, workflow-schedule, workflow-trigger, version.

## Sub-commands

(aiflow-cli-config)=

### config

Manages configuration.

```
aiflow config [-h] COMMAND ... 
```

#### Positional Arguments

> COMMAND

Possible choices: get-value, init, list.

#### Sub-commands

##### get-value

Gets the option value of the configuration.

```
aiflow config get-value [-h] option
```
 
###### Positional Arguments

> option

The option name of the configuration.

##### init

Initializes the default configuration.

```
aiflow config init [-h]
```

##### list

Lists all options of the configuration.

```
aiflow config list [-h] [--color {auto,off,on}]
```

###### Named Arguments

> --color

Possible choices: auto, off, on  
Do emit colored output (default: auto).  
Default: "auto".

(aiflow-cli-db)=

### db

Database operations

```
aiflow db [-h] COMMAND ...
```

#### Positional Arguments

> COMMAND

Possible choices: downgrade, init, reset, upgrade.

#### Sub-commands

##### downgrade

Downgrades the metadata database to the version.

```
aiflow db downgrade [-h] [-v VERSION]
```

###### Named Arguments

> -v, --version

The version corresponding to the database.
Default: "heads".

##### init

Initializes the metadata database.

```
aiflow db init [-h]
```

##### reset

Burns down and rebuild the metadata database.

```
aiflow db reset [-h] [-y]
```

###### Named Arguments

> -y, --yes

Do not prompt to confirm reset. Use with care!
Default: False.

##### upgrade

Upgrades the metadata database to the version

```
aiflow db upgrade [-h] [-v VERSION]
```

###### Named Arguments

> -v, --version

The version corresponding to the database.  
Default: "heads".

(aiflow-cli-namespace)=

### namespace

Namespace related operations.

```
aiflow namespace [-h] COMMAND ...
```

#### Positional Arguments

> COMMAND

Possible choices: add, delete, list.

#### Sub-commands

##### add

Creates a namespace with specific name.

```
aiflow namespace add [-h] [--properties PROPERTIES] namespace_name
```

###### Positional Arguments

> namespace_name

The name of the namespace.

###### Named Arguments

> --properties

Properties of namespace, which is a string in json format.

##### delete

Deletes a namespace with specific name.

```
aiflow namespace delete [-h] [-y] namespace_name
```

###### Positional Arguments

> namespace_name

The name of the namespace.

###### Named Arguments

> -y, --yes

Do not prompt to confirm reset. Use with care!
Default: False.

##### list

Lists all the namespaces.

```
aiflow namespace list [-h] [-o table, json, yaml]
```

###### Named Arguments

> -o, --output

Possible choices: table, json, yaml, plain.  
Output format. Allowed values: json, yaml, plain, table (default: table).  
Default: "table".

(aiflow-cli-server)=

### server

AIFlow server operations.

```
aiflow server [-h] COMMAND ...
```

#### Positional Arguments

> COMMAND

Possible choices: start, stop.

#### Sub-commands

##### start

Starts the AIFlow server.

```
aiflow server start [-h] [-d]
```

###### Named Arguments

> -d, --daemon

Daemonizes instead of running in the foreground.

##### stop

Stops the AIFlow server.

```
aiflow server stop [-h]
```

(aiflow-cli-workflow)=

### workflow

Workflow related operations.

```
aiflow workflow [-h] COMMAND ...
```

#### Positional Arguments

> COMMAND

Possible choices: delete, list, disable, enable, show, upload.

#### Sub-commands

##### delete

Deletes all DB records related to the specified workflow.

```
aiflow workflow delete [-h] [-n NAMESPACE] [-y] workflow_name
```

###### Positional Arguments

> workflow_name

The name of the workflow.

###### Named Arguments

> -n, --namespace

Namespace that contains the workflow.

> -y, --yes

Do not prompt to confirm reset. Use with care!  
Default: False.

##### list

Lists all the workflows.

```
aiflow workflow list [-h] [-n NAMESPACE] [-o table, json, yaml]
```

###### Named Arguments

> -n, --namespace

Namespace that contains the workflow.

> -o, --output

Possible choices: table, json, yaml, plain.  
Output format. Allowed values: json, yaml, plain, table (default: table).  
Default: "table".

##### disable

Disables the workflow so that no more executions would be scheduled.

```
aiflow workflow disable [-h] [-n NAMESPACE] workflow_name
```

###### Positional Arguments

> workflow_name

The name of the workflow.

###### Named Arguments

> -n, --namespace

Namespace that contains the workflow.

> -o, --output

Possible choices: table, json, yaml, plain.  
Output format. Allowed values: json, yaml, plain, table (default: table).  
Default: "table".

##### enable

Enables the workflow which is disabled before.

```
aiflow workflow enable [-h] [-n NAMESPACE] workflow_name
```

###### Positional Arguments

> workflow_name

The name of the workflow.

###### Named Arguments

> -n, --namespace

Namespace that contains the workflow.

##### show

Shows the details of the workflow by workflow name.

```
aiflow workflow show [-h] [-n NAMESPACE] [-o table, json, yaml] workflow_name
```

###### Positional Arguments

> workflow_name

The name of the workflow.

###### Named Arguments

> -n, --namespace

Namespace that contains the workflow.

> -o, --output

Possible choices: table, json, yaml, plain.  
Output format. Allowed values: json, yaml, plain, table (default: table).  
Default: "table".

##### upload

Upload the workflow to the server along with artifacts.

```
aiflow workflow upload [-h] [-f FILES] file_path
```

###### Positional Arguments

> file_path

The path of the workflow file

###### Named Arguments

> -f, --files

Comma separated paths of files that would be uploaded along with the workflow.

(aiflow-cli-workflow-execution)=

### workflow-execution

Workflow execution related operations.

```
aiflow workflow-execution [-h] COMMAND ...
```

#### Positional Arguments

> COMMAND

Possible choices: delete, list, show, start, stop, stop-all.

#### Sub-commands

##### delete

Deletes the workflow execution by execution id.

```
aiflow workflow-execution delete [-h] [-y] workflow_execution_id
```

###### Positional Arguments

> workflow_execution_id

The id of the workflow execution.

###### Named Arguments

> -y, --yes

Do not prompt to confirm reset. Use with care!
Default: False.

##### list

Lists all workflow executions of the workflow.

```
aiflow workflow-execution list [-h] [-n NAMESPACE] [-o table, json, yaml] workflow_name
```

###### Positional Arguments

> workflow_name

The name of workflow.

###### Named Arguments

> -n, --namespace

Namespace that contains the workflow.

> -o, --output

Possible choices: table, json, yaml, plain.  
Output format. Allowed values: json, yaml, plain, table (default: table).  
Default: "table".

##### show

Shows the details of the workflow execution by execution id.

```
aiflow workflow-execution show [-h] [-o table, json, yaml] workflow_execution_id
```

###### Positional Arguments

> workflow_execution_id

The id of the workflow execution

###### Named Arguments

> -o, --output

Possible choices: table, json, yaml, plain.  
Output format. Allowed values: json, yaml, plain, table (default: table).  
Default: "table".

##### start

Starts a new execution of the workflow.

```
aiflow workflow-execution start [-h] [-n NAMESPACE] workflow_name
```

###### Positional Arguments

> workflow_name

The name of workflow.

###### Named Arguments

> -n, --namespace

Namespace that contains the workflow.

##### stop

Stops the workflow execution by execution id.

```
aiflow workflow-execution stop [-h] workflow_execution_id
```

###### Positional Arguments

> workflow_execution_id

The id of the workflow execution.

##### stop-all

Stops all workflow executions of the workflow.

```
aiflow workflow-execution stop-all [-h] [-n NAMESPACE] [-y] workflow_name
```

###### Positional Arguments

> workflow_name

The name of workflow.

###### Named Arguments

> -n, --namespace

Namespace that contains the workflow.

> -y, --yes

Do not prompt to confirm reset. Use with care!
Default: False.

(aiflow-cli-task-execution)=

### task-execution

Task execution related operations.

```
aiflow task-execution [-h] COMMAND ...
```

#### Positional Arguments

> COMMAND

Possible choices: list, show, start, stop.

#### Sub-commands

##### list

Lists all task executions of the workflow execution.

```
aiflow task-execution list [-h] [-o table, json, yaml] workflow_execution_id
```

###### Positional Arguments

> workflow_execution_id

The id of the workflow execution.

###### Named Arguments

> -o, --output

Possible choices: table, json, yaml, plain.  
Output format. Allowed values: json, yaml, plain, table (default: table).  
Default: "table".

##### show

Shows the details of the task execution by execution id.

```
aiflow task-execution show [-h] [-o table, json, yaml] task_execution_id
```

###### Positional Arguments

> task_execution_id

The id of the task execution.

###### Named Arguments

> -o, --output

Possible choices: table, json, yaml, plain.  
Output format. Allowed values: json, yaml, plain, table (default: table).  
Default: "table".

##### start

Starts a new execution of the task of the workflow execution.

```
aiflow task-execution start [-h] workflow_execution_id task_name
```

###### Positional Arguments

> workflow_execution_id

The id of the workflow execution.

> task_name

The name of the task.

##### stop

Stops the task execution by execution id.

```
aiflow task-execution stop [-h] workflow_execution_id task_name
```

###### Positional Arguments

> workflow_execution_id

The id of the workflow execution.

> task_name

The name of the task.

(aiflow-cli-workflow-schedule)=

### workflow-schedule

Manages the periodic schedules of the workflow.

```
aiflow workflow-schedule [-h] COMMAND ...
```

#### Positional Arguments

> COMMAND

Possible choices: add, delete, delete-all, list, pause, resume, show.

#### Sub-commands

##### add

Creates a new schedule for workflow.

```
aiflow workflow-schedule add [-h] [-n NAMESPACE] workflow_name expression
```

###### Positional Arguments

> workflow_name

The name of workflow.

> expression

The expression of the workflow schedule.

###### Named Arguments

> -n, --namespace

Namespace that contains the workflow.

##### delete

Deletes the workflow schedule by id.

```
aiflow workflow-schedule delete [-h] [-y] workflow_schedule_id
```

###### Positional Arguments

> workflow_schedule_id

The id of the workflow schedule.

###### Named Arguments

> -y, --yes

Do not prompt to confirm reset. Use with care!
Default: False.

##### delete-all

Deletes all schedules of the workflow.

```
aiflow workflow-schedule delete-all [-h] [-n NAMESPACE] [-y] workflow_name
```

###### Positional Arguments

> workflow_name

The name of workflow.

###### Named Arguments

> -n, --namespace

Namespace that contains the workflow.

> -y, --yes

Do not prompt to confirm reset. Use with care!
Default: False.

##### list

Lists all schedules of the workflow.

```
aiflow workflow-schedule list [-h] [-n NAMESPACE] [-o table, json, yaml] workflow_name
```

###### Positional Arguments

> workflow_name

The name of workflow.

###### Named Arguments

> -n, --namespace

Namespace that contains the workflow.

> -o, --output

Possible choices: table, json, yaml, plain.  
Output format. Allowed values: json, yaml, plain, table (default: table).  
Default: "table".

##### pause

Pauses the schedule and the workflow would not periodically execute anymore.

```
aiflow workflow-schedule pause [-h] workflow_schedule_id
```

###### Positional Arguments

> workflow_schedule_id

The id of the workflow schedule.

##### resume

Resumes the schedule which is paused before.

```
aiflow workflow-schedule resume [-h] workflow_schedule_id
```

###### Positional Arguments

> workflow_schedule_id

The id of the workflow schedule.

##### show

Shows the details of the workflow schedule by id.

```
aiflow workflow-schedule show [-h] [-o table, json, yaml] workflow_schedule_id
```

###### Positional Arguments

> workflow_schedule_id

The id of the workflow schedule.

###### Named Arguments

> -o, --output

Possible choices: table, json, yaml, plain.  
Output format. Allowed values: json, yaml, plain, table (default: table).  
Default: "table".

(aiflow-cli-workflow-trigger)=

### workflow-trigger

Manages the event triggers of the workflow.

```
aiflow workflow-trigger [-h] COMMAND ...
```

#### Positional Arguments

> COMMAND

Possible choices: delete, delete-all, list, pause, resume, show.

#### Sub-commands

##### delete

Deletes the workflow event trigger by id.

```
aiflow workflow-trigger delete [-h] [-y] workflow_trigger_id
```

###### Positional Arguments

> workflow_trigger_id

The id of the workflow trigger.

###### Named Arguments

> -y, --yes

Do not prompt to confirm reset. Use with care!
Default: False.

##### delete-all

Deletes all event triggers of the workflow.

```
aiflow workflow-trigger delete-all [-h] [-n NAMESPACE] [-y] workflow_name
```

###### Positional Arguments

> workflow_name

The name of workflow.

###### Named Arguments

> -n, --namespace

Namespace that contains the workflow.

> -y, --yes

Do not prompt to confirm reset. Use with care!
Default: False.

##### list

Lists all event triggers of the workflow.

```
aiflow workflow-trigger list [-h] [-n NAMESPACE] [-o table, json, yaml] workflow_name
```

###### Positional Arguments

> workflow_name

The name of workflow.

###### Named Arguments

> -n, --namespace

Namespace that contains the workflow.

> -o, --output

Possible choices: table, json, yaml, plain.  
Output format. Allowed values: json, yaml, plain, table (default: table).  
Default: "table".

##### pause

Pauses the event trigger by id.

```
aiflow workflow-trigger pause [-h] workflow_trigger_id
```

###### Positional Arguments

> workflow_trigger_id

The id of the workflow trigger.

##### resume

Resumes the event trigger by id.

```
aiflow workflow-trigger resume [-h] workflow_trigger_id
```

###### Positional Arguments

> workflow_trigger_id

The id of the workflow trigger.

##### show

Shows the details of the workflow event trigger by id.

```
aiflow workflow-trigger show [-h] [-o table, json, yaml] workflow_trigger_id
```

###### Positional Arguments

> workflow_trigger_id

The id of the workflow trigger.

###### Named Arguments

> -o, --output

Possible choices: table, json, yaml, plain.  
Output format. Allowed values: json, yaml, plain, table (default: table).  
Default: "table".

(aiflow-cli-webserver)=

### webserver

AIFlow Webserver operations.

```
aiflow webserver [-h] COMMAND ...
```

#### Positional Arguments

> COMMAND

Possible choices: start, stop.

#### Sub-commands

##### start

Starts the AIFlow Webserver.

```
aiflow webserver start [-h] [-d]
```

###### Named Arguments

> -d, --daemon

Daemonizes instead of running in the foreground.

##### stop

Stops the AIFlow Webserver

```
aiflow webserver stop [-h]
```

### version

Shows the version.

```
aiflow version [-h]
```


