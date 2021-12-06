# AIFlow

## Command Line Interface

AIFlow has a very rich command-line interface that supports many types of operations on a Workflow, starting services and testing.

**Content**

* Positional Arguments
* Sub-commands:  

  * [server](aiflow-cli-server)
  * [workflow](aiflow-cli-workflow)
  * [job](aiflow-cli-job)
  * [config](aiflow-cli-config)
  * [db](aiflow-cli-db)
  * [version](aiflow-cli-version)
  * [webserver](aiflow-cli-webserver)

### aiflow

```
usage: aiflow [-h] COMMAND ... 
```

### Positional Arguments

> GROUP_OR_COMMAND

Possible choices: server, workflow, job, config, db, version, webserver.

### Sub-commands

(aiflow-cli-server)=

#### server

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

##### Named Arguments

> -d, --daemon

Daemonizes instead of running in the foreground.

##### stop

Stops the AIFlow server.

```
aiflow server stop [-h]
```

(aiflow-cli-workflow)=

#### workflow

Manages workflows of the given project.

```
aiflow workflow [-h] COMMAND ...
```

#### Positional Arguments

> COMMAND

Possible choices: delete, list, list-executions, pause-scheduling, resume-scheduling, show, show-execution, start-execution, stop-execution, submit.

#### Sub-commands

##### delete

Deletes all DB records related to the specified workflow.

```
aiflow workflow delete [-h] [-y] project_path workflow_name
```

##### Positional Arguments

> project_path

The path of the project.

> workflow_name

The name of the workflow.

##### Named Arguments

> -y, --yes

Do not prompt to confirm reset. Use with care!  
Default: False.

##### list

Lists all the workflows.

```
aiflow workflow list [-h] [-o table, json, yaml, plain] project_path
```

##### Positional Arguments

> project_path

The path of the project.

##### Named Arguments

> -o, --output

Possible choices: table, json, yaml, plain.  
Output format. Allowed values: json, yaml, plain, table (default: table).  
Default: "table".

##### list-executions

Lists all workflow executions of the workflow by workflow name.

```
aiflow workflow list-executions [-h] [-o table, json, yaml, plain] project_path workflow_name
```

##### Positional Arguments

> project_path

The path of the project.

> workflow_name

The name of the workflow.

##### Named Arguments

> -o, --output

Possible choices: table, json, yaml, plain.  
Output format. Allowed values: json, yaml, plain, table (default: table).  
Default: "table".

##### pause-scheduling

Pauses a workflow scheduling.

```
aiflow workflow pause-scheduling [-h] project_path workflow_name
```

##### Positional Arguments

> project_path

The path of the project.

> workflow_name

The name of the workflow.

##### resume-scheduling

Resumes a paused workflow scheduling.

```
aiflow workflow resume-scheduling [-h] project_path workflow_name
```

##### Positional Arguments

> project_path

The path of the project.

> workflow_name

The name of the workflow.

##### show

Shows the workflow by workflow name.

```
aiflow workflow show [-h] [-o table, json, yaml, plain] project_path workflow_name 
```

##### Positional Arguments

> project_path

The path of the project.

> workflow_name

The name of the workflow.

##### Named Arguments

> -o, --output

Possible choices: table, json, yaml, plain.  
Output format. Allowed values: json, yaml, plain, table (default: table).  
Default: "table".

##### show-execution

Shows the workflow execution by workflow execution id.

```
aiflow workflow show-execution [-h] [-o table, json, yaml, plain] project_path workflow_execution_id 
```

##### Positional Arguments

> project_path

The path of the project.

> workflow_execution_id

The id of the workflow execution.

##### Named Arguments

> -o, --output

Possible choices: table, json, yaml, plain.  
Output format. Allowed values: json, yaml, plain, table (default: table).  
Default: "table".

##### start-execution

Starts a new workflow execution by workflow name.

```
aiflow workflow start-execution [-h] [-c CONTEXT] project_path workflow_name 
```

##### Positional Arguments

> project_path

The path of the project.

> workflow_name

The name of the workflow.

##### Named Arguments

> -c, --context

The context of the workflow execution to start.

##### stop-execution

Stops the workflow execution by workflow execution id.

```
aiflow workflow stop-execution [-h] project_path workflow_execution_id 
```

##### Positional Arguments

> project_path

The path of the project.

> workflow_execution_id

The id of the workflow execution.

##### stop-executions

Stops all workflow executions by workflow name.

```
aiflow workflow stop-executions [-h] project_path workflow_name 
```

##### Positional Arguments

> project_path

The path of the project.

> workflow_name

The name of the workflow.

##### submit

Submits the workflow by workflow name.

```
aiflow workflow submit [-h] project_path workflow_name  
```

##### Positional Arguments

> project_path

The path of the project.

> workflow_name

The name of the workflow.

(aiflow-cli-job)=

#### job

Manages jobs of the given project.

```
aiflow job [-h] COMMAND ...
```

#### Positional Arguments

> COMMAND

Possible choices: list-executions, restart-execution, show-execution, start-execution, stop-execution.

#### Sub-commands

##### list-executions

Lists all job executions of the workflow execution by workflow execution id.

```
aiflow job list-executions [-h] [-o table, json, yaml, plain] project_path workflow_execution_id
```

##### Positional Arguments

> project_path

The path of the project.

> workflow_execution_id

The id of the workflow execution.

##### Named Arguments

> -o, --output

Possible choices: table, json, yaml, plain.  
Output format. Allowed values: json, yaml, plain, table (default: table).  
Default: "table".

##### restart-execution

Restarts the job execution by job name and workflow execution id.

```
aiflow job restart-execution [-h] project_path job_name workflow_execution_id 
```

##### Positional Arguments

> project_path

The path of the project.

> job_name

The name of the job.

> workflow_execution_id

The id of the workflow execution.

###### show-execution

Shows the job execution by job name and workflow execution id.

```
aiflow job show-execution [-h] [-o table, json, yaml, plain] project_path job_name workflow_execution_id
```

##### Positional Arguments

> project_path

The path of the project.

> job_name

The name of the job.

> workflow_execution_id

The id of the workflow execution.

##### Named Arguments

> -o, --output

Possible choices: table, json, yaml, plain.  
Output format. Allowed values: json, yaml, plain, table (default: table).  
Default: "table".

##### start-execution

Starts the job execution by job name and workflow execution id.

```
aiflow job start-execution [-h] project_path job_name workflow_execution_id 
```

##### Positional Arguments

> project_path

The path of the project.

> job_name

The name of the job.

> workflow_execution_id

The id of the workflow execution.

##### stop-execution

Stops the job execution by job name and workflow execution id.

```
aiflow job stop-execution [-h] project_path job_name workflow_execution_id
```

##### Positional Arguments

> project_path

The path of the project.

> job_name

The name of the job.

> workflow_execution_id

The id of the workflow execution.

(aiflow-cli-config)=

#### config

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
 
##### Positional Arguments

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

##### Named Arguments

> --color

Possible choices: auto, off, on  
Do emit colored output (default: auto).  
Default: "auto".

(aiflow-cli-db)=

#### db

Database operations

```
aiflow db [-h] COMMAND ...
```

#### Positional Arguments

> COMMAND

Possible choices: downgrade, init, reset, upgrade.

##### Sub-commands

##### downgrade

Downgrades the metadata database to the version.

```
aiflow db downgrade [-h] [-v VERSION]
```

##### Named Arguments

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

##### Named Arguments

> -y, --yes

Do not prompt to confirm reset. Use with care!
Default: False.

##### upgrade

Upgrades the metadata database to the version

```
aiflow db upgrade [-h] [-v VERSION]
```

#### Named Arguments

> -v, --version

The version corresponding to the database.  
Default: "heads".

(aiflow-cli-version)=

#### version

Shows the version.

```
aiflow version [-h]
```

(aiflow-cli-webserver)=

#### webserver

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

##### Named Arguments

> -d, --daemon

Daemonizes instead of running in the foreground.

##### stop

Stops the AIFlow Webserver

```
aiflow webserver stop [-h]
```
