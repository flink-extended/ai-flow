# Deploying AIFlow Server

In this guide, we demonstrate how to deploy an AIFlow server.

```{note}
If you use Airflow as the scheduler, the AIFlow server should run on the same machine with the Airflow
Scheduler, as they rely on the filesystem to submit workflows.
```

## Starting an AIFlow server

In this section, we will show you how to use the default configuration to start an AIFlow server.

### Generate default configuration

To generate the default configuration of AIFlow server, you can run the following command:

```bash
init-aiflow-env.sh
```

This command will generate the [default configuration](default_aiflow_server_config) file `aiflow_server.yaml` in
the `$AIFLOW_HOME` directory or `$HOME/aiflow` directory if `$AIFLOW_HOME` is not set.

```{note}
If the config file already exist, the script will not overwrite the config. If you intend to overwrite 
your existing config, you need to remove it manually and then run the script again.
```

You can refer to [here](configuration) if you want to learn all the configuration you can change.

### Start the AIFlow server

```{note}
AIFlow server requires notification server to work. Please make sure you have 
[deployed a notification server](./notification_server.md) and configure the notification uri in the AIFlow server 
config file accordingly. 
```

You can start the AIFlow server with the following command.

```bash
start-aiflow.sh
```

It will start the AIFlow server and AIFlow web server in background processes. You can check the log at
`$AIFLOW_HOME/logs` or `$HOME/aiflow/logs` directory. The pid of the background process is stored at 
`$AIFLOW_HOME` or `$HOME/aiflow/logs` directory. 

The AIFlow web server listen on port 8000 by default. If you didn't change the port in the configuration you can visit
http://127.0.0.1:8000 to see the AIFlow web server UI.

(configuration)=
## Configuration

This section shows an exhaustive list of available configuration of the AIFlow server.

### AIFlow server

|Key|Type|Default|Description|
|---|---|---|---|
|server_port|Integer|50051|The port where the AIFlow server is exposed.|
|db_uri|String|sqlite:///${AIFLOW_HOME}/aiflow.db|The uri of the database backend for AIFlow server.|
|db_type|String|SQL_LITE|The type of the database backend for AIFlow server. It can be SQL_LITE, MYSQL, MONGODB.|
|notification_server_uri|String|127.0.0.1:50052|The uri of the notification server that the AIFlow server connect to.|
|start_meta_service|Boolean|True|Whether to start the metadata service in AIFlow server.|
|start_model_center_service|Boolean|True|Whether to start the model center service in AIFlow server.|
|start_metric_service|Boolean|True|Whether to start the metric service in AIFlow server.|
|start_scheduler_service|Boolean|True|Whether to start the scheduler service in AIFlow server.|
|scheduler_service|Dict| |The configuration of the [Scheduler Service](scheduler_service).|
|web_server|Dict| |The configuration of the [AIFlow Web Server](aiflow_web_server). |

(scheduler_service)=

### Scheduler Service

|Key|Type|Default|Description|
|---|---|---|---|
|scheduler|Dict| |The configuration of the [Scheduler](scheduler).|

(scheduler)=

### Scheduler

|Key|Type|Default|Description|
|---|---|---|---|
|scheduler_class|String|ai_flow_plugins.scheduler_plugins.airflow.airflow_scheduler.AirFlowScheduler|The class of the scheduler plugin.|
|scheduler_config|Dict| |Configuration of the scheduler plugin implementation. The configuration of [Airflow Scheduler](airflow_scheduler).|

(airflow_scheduler)=

### Airflow Scheduler

|Key|Type|Default|Description|
|---|---|---|---|
|airflow_deploy_path|String|(none)|AirFlow dag file deployment directory, i.e., where to submit the Airflow dag file. If it is not set, the dags_folder in airflow config will be used.|
|notification_server_uri|String|(none)|The notification server uri used by the AirflowScheduler.|

(aiflow_web_server)=

### AIFlow Web Server

|Key|Type|Default|Description|
|---|---|---|---|
airflow_web_server_uri|String|http://localhost:8080|The Airflow web server uri.|
host|String|127.0.0.1|The hostname the AIFlow Web server to listen on. Set this to ``'0.0.0.0'`` to have the server available externally as well.|
port|Integer|8000|The port where the AIFlow Web server is exposed.|

(default_aiflow_server_config)=

## Default AIFlow server Configuration example

```yaml
# Config of AIFlow server

# port of AIFlow server
server_port: 50051
# uri of database backend for AIFlow server
db_uri: sqlite:///{AIFLOW_HOME}/aiflow.db
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

# web server config
web_server:
  airflow_web_server_uri: http://localhost:8080
  host: 127.0.0.1
  port: 8000
```
