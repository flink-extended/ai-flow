# Deployment

## Overview

In this guide, we will demonstrate how to deploy AIFlow with Airflow as the scheduler and MySQL as the database.

The image below shows the components of an AIFlow deployment.

AIFlow Server is the main component, which is responsible for submitting workflows to the scheduler, manage the life
cycle of the workflows, and bookkeeping the metadata of the AIFlow projects. Notification service is used to handle
event sending and event listening. The scheduler should support event-based scheduling and is responsible for scheduling
the workflow. All the components above need a database, and we use MySQL as the database.

![Alt text](../images/AIFlow-Deploy-Overview.png)

## Install AIFlow

Before we start deploying the components, you need to install the AIFlow. Please refer to
[Install AIFlow](installation.md) for the installation guide.

## Database setup

Before we start deploying AIFlow, let's create the database we are going to use. In this guide, we will create one
database for each component. You can create the database with the following command:

```bash
CREATE DATABASE airflow CHARACTER SET UTF8mb3 COLLATE utf8_general_ci;
CREATE DATABASE aiflow CHARACTER SET UTF8mb3 COLLATE utf8_general_ci;
CREATE DATABASE notification CHARACTER SET UTF8mb3 COLLATE utf8_general_ci;
```

## Notification Service

### Configuration

To start the Notification server, you need to prepare a configuration file, `notification_server.yaml`. Notification
server will look for the `notification_server.yaml` in the `$NOTIFICATION_HOME` directory
or `$HOME/notification_service`
directory if `$NOTIFICATION_HOME` is not set. Therefore, you should have the `notification_server.yaml` in the right
place. And the configuration file we will be using is the following.

```yaml
# port of notification server
server_port: 50052
# uri of database backend for notification server
db_uri: mysql://username:password@database/notification
# High availability is disabled by default
enable_ha: false
# TTL of the heartbeat of a server, i.e., if the server hasn't sent heartbeat for the TTL time, it is down.
ha_ttl_ms: 10000
# Hostname and port the server will advertise to clients. If not set, it will use the local ip and configured port.
advertised_uri: 127.0.0.1:50052
```

### Start the notification server

To start the notification service, you can run the `start-notification.py` script. It will start the notification in a
background process. You can check the log of the notification server at `$NOTIFICATION_HOME/logs` directory. If you
see "
Notification server started." in the log, the notification service is successfully started.

## Airflow As Scheduler

We use enhanced Airflow as an event-based scheduler and both
[LocalExecutor](https://airflow.apache.org/docs/apache-airflow/stable/executor/local.html) and
[CeleryExecutor](https://airflow.apache.org/docs/apache-airflow/stable/executor/celery.html) are supported. Follow below
steps to initialize configuration and start the Airflow scheduler.

### LocalExecutor

1. Prepare the default Airflow configuration. The following script will generate a default Airflow configuration
   file, `airflow.cfg` at the `$AIRFLOW_HOME` directory or `$HOME/airflow` directory if `$AIRFLOW_HOME` is not set.

   ```bash
   init-airflow-env.sh
   ```

2. Modify configuration file. You need to change the `sql_alchemy_conn` to `mysql://username:password@database/airflow`
   use the mysql database.

3. Start the Scheduler

   ```bash
   start-airflow.sh
   ```

### CeleryExecutor

1. Prepare broker and backend. Celery needs a broker and a result backend to distribute and store tasks. For more
   information about setting up the broker and result backend, refer to the exhaustive
   [Celery documentation on the topic](https://docs.celeryproject.org/en/latest/getting-started/).

2. Set environment variables

   ```
   export AIRFLOW_HOME=~/airflow/home
   export MYSQL_CONN=mysql://username:password@database/table
   
   # You need to set the broker and result backend to the value you set up in step1. 
   # E.g. set both broker and result backend to redis://redis:6379/0.
   export BROKER_URL=redis://redis:6379/0
   export RESULT_BACKEND=redis://redis:6379/0
   ```

3. Prepare the Airflow configuration. To enable CeleryExecutor of the scheduler, you need to run the following command
   on scheduler server and all celery workers to make sure the configurations among hosts are equivalent. The broker URL
   and result backend you set up should be passed as well.

   ```bash
   init-airflow-with-celery-executor.sh $MYSQL_CONN $BROKER_URL $RESULT_BACKEND
   ```

4. Start Celery cluster.

   ```bash
   # Run following command on every Celery node in cluster, you may see ```celery@node_id ready.``` once worker started successfully.
   airflow celery worker
   ```

5. Start the Scheduler

   ```bash
   start-airflow.sh
   ```

## AIFlow Server

AIFlow server and the airflow scheduler should run on the same machine, as they rely on the filesystem to submit
workflow.

### Configuration

To start an AIFlow server, you need to prepare a configuration file, `aiflow_server.yaml`. AIFLow will look for the
`aiflow_server.yaml` in the `$AIFLOW_HOME` directory or `$HOME/aiflow` directory if `$AIFLOW_HOME` is not set. Therefore, you
should have the `aiflow_server.yaml` in the right place. And the configuration file we will be using is the following.

```yaml
# Config of AIFlow server

# port of AIFlow server
server_port: 50051
# uri of database backend for AIFlow server
db_uri: mysql://username:password@database/aiflow
# type of database backend for AIFlow server, can be SQL_LITE, MYSQL, MONGODB
db_type: MYSQL

# High availability is disabled by default
#enable_ha: false
# TTL of the heartbeat of a server, i.e., if the server hasn't send heartbeat for the TTL time, it is down.
#ha_ttl_ms: 10000

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

Note:

- You need to specify the database connection string
- We start the notification service in the previous section, so we set start_default_notification to false. And the
  notification_server_uri must match the notification service we started.

### Start the aiflow server

You can start the aiflow server with the following command.

```bash
start_aiflow.sh
```

It will start the AIFlow server and AIFlow web server in background processes. You can check the log at
`$AIFLOW_HOME/logs` directory. If you see "AIFlow server started" in the log, the AIFlow server is successfully started.