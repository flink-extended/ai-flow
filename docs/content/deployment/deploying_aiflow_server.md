# Deploying AIFlow Server

In this guide, we demonstrate how to deploy an AIFlow Server.

```{note}
If you use Airflow as the scheduler, the AIFlow server should run on the same machine with the Airflow
Scheduler, such that the AIFlow Server can put the Airflow Dag files to the Airflow Scheduler dag folder.
```

## Initialize Configuration

To initialize the default configuration file, you can run the following command:

```bash
aiflow config init
```

This command will generate the [default configuration](default_aiflow_server_config) file `aiflow_server.yaml` in
the `$AIFLOW_HOME` directory(default is `$HOME/aiflow`).

```{note}
If the config file already exists, the command will not generate the default configuration. If you want to reset 
the configration, you need to remove it manually and then run the script again.
```

If you want to learn all configurations, you can refer to [here](configuration).

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

You can start the AIFlow Server and AIFlow web server with the following commands.

```bash
aiflow server start -d

aiflow webserver start -d
```

It will start the AIFlow Server and AIFlow web server in background processes. You can check the log at
`$AIFLOW_HOME/logs` or `$HOME/aiflow/logs` directory. `aiflow-server-*.log` is the log of AIFlow Server
and `aiflow-webserver-*.log` is the log of AIFlow web server.

The AIFlow web server listens on port 8000 by default, and you can visit
http://127.0.0.1:8000 to see the AIFlow web UI.

(configuration)=

## Configuration

This section shows an exhaustive list of available configuration of the AIFlow Server.

### AIFlow server

|Key|Type|Default|Description|
|---|---|---|---|
|server_port|Integer|50051|The port where the AIFlow Server is exposed.|
|db_uri|String|sqlite:///${AIFLOW_HOME}/aiflow.db|The uri of the database backend for AIFlow Server.|
|db_type|String|SQL_LITE|The type of the database backend for AIFlow Server. It can be SQL_LITE, MYSQL, MONGODB.|
|notification_server_uri|String|127.0.0.1:50052|The uri of the Notification Server that the AIFlow Server connect to.|
|start_meta_service|Boolean|True|Whether to start the metadata service in AIFlow Server.|
|start_model_center_service|Boolean|True|Whether to start the model center service in AIFlow Server.|
|start_metric_service|Boolean|True|Whether to start the metric service in AIFlow Server.|
|start_scheduler_service|Boolean|True|Whether to start the scheduler service in AIFlow Server.|
|scheduler_service|Dict|[Scheduler Service](scheduler_service)|The configuration of the [Scheduler Service](scheduler_service).|
|web_server|Dict|[AIFlow Web Server](aiflow_web_server)|The configuration of the [AIFlow Web Server](aiflow_web_server). |

(scheduler_service)=

### Scheduler Service

|Key|Type|Default|Description|
|---|---|---|---|
|scheduler|Dict|[Scheduler](scheduler)|The configuration of the [Scheduler](scheduler).|
|repository|String|/tmp|The path to a local directory where the scheduler service download the Workflow codes.|

(scheduler)=

### Scheduler

|Key|Type|Default|Description|
|---|---|---|---|
|scheduler_class|String|ai_flow_plugins.scheduler_plugins.airflow.airflow_scheduler.AirFlowScheduler|The class of the scheduler plugin.|
|scheduler_config|Dict|[Airflow Scheduler](airflow_scheduler)|Configuration of the scheduler plugin implementation. The configuration of [Airflow Scheduler](airflow_scheduler).|

(airflow_scheduler)=

### Airflow Scheduler

|Key|Type|Default|Description|
|---|---|---|---|
|airflow_deploy_path|String|(none)|Airflow dag file deployment directory, i.e., where to submit the Airflow dag file. If it is not set, the dags_folder in airflow config will be used.|
|notification_server_uri|String|(none)|The Notification Server uri used by the AirflowScheduler.|

(aiflow_web_server)=

### AIFlow Web Server

|Key|Type|Default|Description|
|---|---|---|---|
airflow_web_server_uri|String|http://localhost:8080|The Airflow web server uri.|
host|String|0.0.0.0|The hostname the AIFlow Web server to listen on.|
port|Integer|8000|The port where the AIFlow Web server is exposed.|

(default_aiflow_server_config)=

## Default AIFlow server Configuration example

```yaml
# Config of AIFlow server

# port of AIFlow server
server_port: 50051
# uri of database backend for AIFlow server
db_uri: sqlite:///${AIFLOW_HOME}/aiflow.db
# type of database backend for AIFlow server, can be SQL_LITE, MYSQL, MONGODB
db_type: SQL_LITE

# uri of the server of notification service
notification_server_uri: 127.0.0.1:50052

# whether to start the metadata service, default is True
#start_meta_service: True

# whether to start the model center service, default is True
#start_model_center_service: True

# whether to start the metric service, default is True
#start_metric_service: True

# whether to start the scheduler service, default is True
#start_scheduler_service: True

# scheduler config
scheduler_service:
  scheduler:
    scheduler_class: ai_flow_plugins.scheduler_plugins.airflow.airflow_scheduler.AirFlowScheduler
    scheduler_config:
      # AirFlow dag file deployment directory, i.e., where the airflow dag will be. If it is not set, the dags_folder in
      # airflow config will be used
      #airflow_deploy_path: /tmp/dags

      # Notification service uri used by the AirFlowScheduler.
      notification_server_uri: 127.0.0.1:50052
  # The path to a local directory where the scheduler service download the Workflow codes.
  #repository: /tmp

# web server config
web_server:
  airflow_web_server_uri: http://localhost:8080
  host: 0.0.0.0
  port: 8000
```
```{note}
The variable `${AIFLOW_HOME}` in above configuration should be replaced with your own path.
```
