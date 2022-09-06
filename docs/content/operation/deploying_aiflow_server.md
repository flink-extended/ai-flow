# Deploying AIFlow Server

In this guide, we demonstrate how to deploy an AIFlow Server.

## Initialize Configuration

To initialize the default configuration file, you can run the following command:

```bash
aiflow config init
```

This command will generate the default configuration file `aiflow_server.yaml` in
the `$AIFLOW_HOME` directory(`$HOME/aiflow` by default).

```{note}
If the config file already exists, the command will not generate the default configuration. If you want to reset 
the configration, you need to remove it manually and then run the script again.
```

If you want to learn all configurations, you can refer to [here](#configuration).

## Initialize Database
The database uri of AIFlow Server is configured in `aiflow_server.yaml`, you can run following command to initialize database.
```bash
aiflow db init
```

## Start the AIFlow Server

```{note}
AIFlow Server requires Notification Server to work. Please make sure you have 
deployed a notification server and configure the notification uri in the AIFlow Server 
config file accordingly. 
```

You can start the AIFlow Server with the following commands.

```bash
aiflow server start -d
```

It will start the AIFlow Server in background processes. You can check the log at
`$AIFLOW_HOME/logs` directory.


(configuration)=

## Configuration

This section shows an exhaustive list of available configuration of the AIFlow Server.

### AIFlow server

|Key|Type|Default|Description|
|---|---|---|---|
|log_dir|String|${AIFLOW_HOME}|The base log folder of the scheduler and job executions.|
|rpc_port|Integer|50051|The rpc port where the AIFlow server is exposed to client.|
|internal_rpc_port|Integer|50000|The rpc port where the AIFlow server exposed for internal communication.|
|rest_port|Integer|8000|The port where the AIFlow rest server exposed.|
|metadata_backend_uri|String|sqlite:///${AIFLOW_HOME}/aiflow.db|The uri of the database backend for AIFlow Server.|
|state_backend_uri|String|sqlite:///${AIFLOW_HOME}/aiflow.db|The uri of the state backend.|
|sql_alchemy_pool_enabled|Boolean|True|Whether SqlAlchemy enables pool database connections.|
|sql_alchemy_pool_size|Integer|5|The maximum number of database connections in the pool. 0 indicates no limit.|
|sql_alchemy_max_overflow|Integer|10|The maximum overflow size of the pool.|
|history_retention|String|30d|Metadata and log history retention.|
|notification_server_uri|String|127.0.0.1:50052|The uri of the Notification Server that the AIFlow Server connect to.|

### Task Executor
|Key|Type|Default|Description|
|---|---|---|---|
|task_executor|String|Local|The executor to run tasks.|
|task_executor_heartbeat_check_interval|Integer|10|The interval in seconds that the task executor check the heartbeat of task executions.|
|task_heartbeat_interval|Integer|10|The interval in seconds that the task executions send heartbeats.|
|task_heartbeat_timeout|Integer|60|The timeout in seconds that the task executions is treated as timeout.|
|local_executor_parallelism|Integer|10|Num of workers of local task executor.|

## Default AIFlow server Configuration

```yaml
# directory of AIFlow logs
log_dir : {AIFLOW_HOME}/logs

# port of rpc server
rpc_port: 50051

# port of internal rpc
internal_rpc_port: 50000

# port of rest server
rest_port: 8000

# uri of database backend for AIFlow server
metadata_backend_uri: sqlite:///{AIFLOW_HOME}/aiflow.db

# metadata and log history retention
history_retention: 30d

# uri of state backend
state_backend_uri: sqlite:///{AIFLOW_HOME}/aiflow.db

# whether SqlAlchemy enables p s.
sql_alchemy_pool_enabled: True

# the maximum number of database connections in the pool. 0 indicates no limit.
sql_alchemy_pool_size: 5

# the maximum overflow size of the pool.
sql_alchemy_max_overflow: 10

# uri of the server of notification service
notification_server_uri: 127.0.0.1:50052

# task executor
task_executor: Local

# the interval in seconds that the task executor check the heartbeat of task executions
task_executor_heartbeat_check_interval: 10

# the timeout in seconds that the task executions is treated as timeout
task_heartbeat_timeout: 60

# the interval in seconds that the task executions send heartbeats
task_heartbeat_interval: 10

# num of workers of local task executor
local_executor_parallelism: 10

# kubernetes task executor config
k8s_executor_config:
  pod_template_file:
  image_repository:
  image_tag:
  namespace:
  in_cluster: False
  kube_config_file:
```
```{note}
The variable `${AIFLOW_HOME}` in above configuration should be replaced with your own path.
```
