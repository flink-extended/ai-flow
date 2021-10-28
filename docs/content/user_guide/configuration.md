# Configuration

This document aims at introducing different kinds of configuration in AI Flow.

   * [AI Flow Server Config](#ai-flow-server-config)
      * [Basic Server Config](#basic-server-config)
      * [Service Config](#service-config)
      * [Experimental Config](#experimental-config)
         * [High Availability](#high-availability)
      * [Scheduler Config](#scheduler-config)
         * [Airflow](#airflow)
   * [AI Flow Project Config](#ai-flow-project-config)
      * [Basic Config](#basic-config)
      * [Blob Manager Config](#blob-manager-config)
         * [Local](#local)
         * [HDFS](#hdfs)
         * [OSS](#oss)
   * [AI Flow Workflow Config](#ai-flow-workflow-config)
      * [Periodic Config](#periodic-config)
      * [User-defined Properties](#user-defined-properties)
      * [Job Config](#job-config)
         * [General Config](#general-config)
         * [Python Job Config](#python-job-config)
         * [Flink Job Config](#flink-job-config)
         * [Bash Job Config](#bash-job-config)



## AI Flow Server Config
The configs of `AIFlowServer()` locate in the `aiflow_server.yaml` in $AIFLOW_HOME/airflow_deploy or `~/aiflow/` directory.
If users want to modify default values of configs, they should update the `aiflow_server.yaml` file and restart the server.

Default `aiflow_server.yaml` can be viewed in the [link](https://github.com/alibaba/flink-ai-extended/blob/master/flink-ai-flow/ai_flow/config_templates/default_aiflow_server.yaml). Here we will talk about more details about some important configs.

### Basic Server Config
```yaml

# endpoint of AIFlow server
server_ip: localhost
server_port: 50051
# uri of database backend for AIFlow server
db_uri: sqlite:///{AIFLOW_HOME}/aiflow.db
# type of database backend for AIFlow server, can be SQL_LITE, MYSQL, MONGODB
db_type: SQL_LITE
```
As above codes suggest, users must make sure the ip and the port of the server available. 
The AIFlow server also needs a database to work properly(e.g. managing workflows). We currently support SQL_LITE, MYSQL and MONGODB.

### Service Config
An AIFlow server contains multiple services: notification service, meta_service, metric_service, scheduler_service. For those services, AI Flow provides default implementations and to control the start of them, users need to pay attention to following configs:
```yaml
# whether to start the default notification service, default is True
# start_default_notification: True
# uri of the notification service. Use the server_ip: server_port if not set.
# notification_uri: localhost:50051

# whether to start the metadata service, default is True
#start_meta_service: True

# whether to start the model center service, default is True
#start_model_center_service: True

# whether to start the metric service, default is True
#start_metric_service: True

# whether to start the scheduler service, default is True
#start_scheduler_service: True

# scheduler config
scheduler:
  scheduler_class: ai_flow_plugins.scheduler_plugins.airflow.airflow_scheduler.AirFlowScheduler
  scheduler_config:
    # AirFlow dag file deployment directory, i.e., where the airflow dag will be.
    airflow_deploy_path: {AIFLOW_HOME}/airflow_deploy
    # Notification service uri used by the scheduler service.
    notification_service_uri: localhost:50051
```
Note, for scheduler config, users must offer the full class name of the scheduler and add necessary configs depending on the type of scheduler they choose. 
Take the `AirFlow` scheduler as an example: 
Users must set the `airflow_deploy_path` and must make sure the `notification_service_uri` is the same with the `notification_uri` used by `AIFlowServer`.


### Experimental Config
#### High Availability
HA is currently an experimental feature of AI Flow. To use this feature, users must set `enable_ha` to be true in `aiflow_server.yaml`.
```yaml
# High availability is disabled by default
#enable_ha: false
# TTL of the heartbeat of a server, i.e., if the server hasn't send heartbeat for the TTL time, it is down.
#ha_ttl_ms: 10000
```

### Scheduler Config
#### Airflow
Airflow is our default scheduler and it needs following configs:
```yaml
scheduler:
  scheduler_class_name: ai_flow_plugins.scheduler_plugins.airflow.airflow_scheduler.AirFlowScheduler
  scheduler_config:
    airflow_deploy_path: /path/to/airflow_deploy
    notification_service_uri: localhost:50051
```

## AI Flow Project Config
For an AI Flow project, we need to set some basic configs and besides, we must set `blob` config to tell AI Flow where the workflow should be executed.

### Basic Config
```yaml
project_name: wide_and_deep
server_ip: localhost
server_port: 50051
notification_uri: localhost:50051
```

### Blob Manager Config
#### Local
```yaml
blob:
  blob_manager_class: ai_flow_plugins.blob_manager_plugins.local_blob_manager.LocalBlobManager
```

#### HDFS
```yaml
blob:
  blob_manager_class: ai_flow_plugins.blob_manager_plugins.hdfs_blob_manager.HDFSBlobManager,
  blob_manager_config:
    local_repository:
    hdfs_url: 
    hdfs_user: 
    repo_name: 
```

#### OSS
```yaml
blob:
  blob_manager_class: ai_flow_plugins.blob_manager_plugins.oss_blob_manager.OssBlobManager
  blob_manager_config:
    access_key_id:
    access_key_secret:
    endpoint: 
    bucket: 
    repo_name: 
    local_repository: 
```

## AI Flow Workflow Config
Workflow config consists of job configs, workflow-level periodic config, user define properties.

### Periodic Config
Periodic config of a workflow will trigger multiple workflow executions. Support two types of periodic configs are supported:
1. cron config
pattern:
```yaml
periodic_config:
  start_date: '2020,1,1,1,1,1,'
  cron: '* * * * * * *'
```
start_date_expression:
`year:int,month:int,day:int,hour:int,minute:int,second:int,Option[tzinfo: str]`

cron_expression:
`seconds minutes hours days months weeks years`

2. interval config 
pattern:
```yaml
periodic_config:
  start_date: '2020,1,1,1,1,1,'
  interval: '0,0,0,60' 
```
start_date_expression:
`year:int,month:int,day:int,hour:int,minute:int,second:int,Option[tzinfo: str]`

interval_expression:
`days:int,hours:int,minutes:int,seconds:int`


### User-defined Properties
```yaml
properties:
  name0: value0
  name1: value1
```

### Job Config
AI Flow currently supports bash, python and flink jobs.

#### General Config
Any job in AI Flow contains following configs:
```yaml
job_name:
  job_type: python
  periodic_config:
    interval: "0,0,0,60"
  properties:
```
Note, the job config is started with the job name(e.g. `train_job`). And under the job name, we can set the type of the job, the properties of the job and the periodic scheduling pattern.

#### Periodic Config
The periodic config of a job shares the same patterns with the workflow-level periodic config. 
The difference is that periodic jobs are triggered and executed periodically in only one workflow execution.


#### Python Job Config
```yaml
python_job_name:
  job_type: python
  properties:
    python_executable_path: /usr/bin/python3
    env:
      a: a
      b: b
```
#### Flink Job Config

```yaml
flink_job_name:
  job_type: flink
  properties:
    run_mode: local or cluster (default local)
    stop_mode: stop or cancel (default cancel)It means to stop the flink job using the (flink stop job_id)
               or (flink cancel job_id) command.
    flink_run_args: The flink run command args(-pym etc.). It's type is List.
      - -pym
      - /usr/lib/python
    flink_stop_args: The flink run command args(--savepointPath etc.). It's type is List.
      - --savepointPath
      - /tmp/savepoint

```
#### Bash Job Config
```yaml
bash_job_name:
  job_type: bash
  properties:
    env:
      a: a
      b: b
```


