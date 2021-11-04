# Deployment

## Overview
In this guide, we will demonstrate how to deploy AIFlow with Airflow as the scheduler and MySQL as the database.

The image below shows the components of an AIFlow deployment. AIFlow Server is the main component, which is responsible for submitting workflows to the scheduler, manage the life cycle of the workflows, and bookkeeping the metadata of the AIFlow projects. Notification service is used to handle event sending and event listening. The scheduler should support event-based scheduling and is responsible for scheduling the workflow. All the components above need a database, and we use MySQL as the database.

![Alt text](../../../images/AIFlow-Deploy-Overview.png)

## Install AIFlow
Before we start deploying the components, you need to install the AIFlow. Please refer to [[Install AIFlow|Install AIFlow]] for the installation guide.

## Database setup
Before we start deploying AIFlow, let's create the database we are going to use. In this guide, we will create one database for each component. You can create the database with the following command:
```
CREATE DATABASE airflow CHARACTER SET UTF8mb3 COLLATE utf8_general_ci;
CREATE DATABASE aiflow CHARACTER SET UTF8mb3 COLLATE utf8_general_ci;
CREATE DATABASE notification CHARACTER SET UTF8mb3 COLLATE utf8_general_ci;
```

## Notification Service

To start the notification service, you can run the start_notification_service.py script.

```
usage: start_notification_service.py [-h] [--port PORT]
                                     [--database-conn DATABASE_CONN]
                                     [--enable-ha ENABLE_HA]
                                     [--server-uri SERVER_URI]

optional arguments:
  -h, --help            show this help message and exit
  --port PORT           The port on which to run notification service， default
                        is 50052
  --database-conn DATABASE_CONN
                        Database connection info
  --enable-ha ENABLE_HA
                        Whether to start a notification service with HA
                        enabled, default is False
  --server-uri SERVER_URI
                        Need to be set when HA is enabled. It should be the
                        URI of local notification server that can be reached
                        from others
```

- Start a notification service with default port
`start_notification_service.py --database-conn=${MYSQL_CONN}`

- Start notification service with ha enabled
`start_notification_service.py --database-conn=${MYSQL_CONN} --enable-ha=true --server_uris=${URIs}`

If you see "Notification master started.", the notification service is successfully started.

## Airflow As Scheduler
We use enhanced Airflow as an event-based scheduler and both [[LocalExecutor|https://airflow.apache.org/docs/apache-airflow/stable/executor/local.html]] and [[CeleryExecutor|https://airflow.apache.org/docs/apache-airflow/stable/executor/celery.html#]] are supported. Follow below steps to initialize configuration and start the Airflow scheduler.

### LocalExecutor
1. Set environment variables.
```
export AIRFLOW_HOME=~/airflow/home
export MYSQL_CONN=mysql://username:password@database/table
```
2. Prepare the Airflow configuration.
```
init-airflow-env.sh ${MYSQL_CONN}
```
3. Start the Scheduler
```
start-airflow.sh $MYSQL_CONN
```

### CeleryExecutor
1. Prepare broker and backend. Celery needs a broker and a result backend to distribute and store tasks. For more information about setting up the broker and result backend, refer to the exhaustive [[Celery documentation on the topic|https://docs.celeryproject.org/en/latest/getting-started/]].

2. Set environment variables
```
export AIRFLOW_HOME=~/airflow/home
export MYSQL_CONN=mysql://username:password@database/table

# You need to set the broker and result backend to the value you set up in step1. 
# E.g. set both broker and result backend to redis://redis:6379/0.
export BROKER_URL=redis://redis:6379/0
export RESULT_BACKEND=redis://redis:6379/0
```

3. Prepare the Airflow configuration. To enable CeleryExecutor of the scheduler, you need to run the following command on scheduler server and all celery workers to make sure the configurations among hosts are equivalent. The broker URL and result backend you set up should be passed as well.
```
init-airflow-with-celery-executor.sh $MYSQL_CONN $BROKER_URL $RESULT_BACKEND
```

4. Start Celery cluster.
```
# Run following command on every Celery node in cluster, you may see ```celery@node_id ready.``` once worker started successfully.
airflow celery worker
```

5. Start the Scheduler
```
start-airflow.sh $MYSQL_CONN
```

## AIFlow Server
AIFlow server and the airflow scheduler should run on the same machine, as they rely on the filesystem to submit workflow.

### Configuration

To start an AIFlow server, you need to prepare a configuration file, `master.yaml`. AIFLow will look for the `master.yaml` in the $AIFLOW_HOME directory or $HOME/aiflow directory if $AIFLOW_HOME is not set. Therefore, you should have the `master.yaml` in the right place. And the configuration file we will be using is the following.

```
# Config of master server

# endpoint of master
server_ip: localhost
server_port: 50051
# uri of database backend for AIFlow
db_uri: mysql://username:password@database/table
# type of database backend in master, can be SQL_LITE, MYSQL, MONGODB
db_type: MYSQL

# High availability is disabled by default
#enable_ha: false
# 
#ha_ttl_ms: 10000

# whether to start the default notification service, default is True
start_default_notification: False
# uri of the notification service. Use the server_ip: server_port if not set.
notification_server_uri: localhost:50052

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
    airflow_deploy_path: ~/aiflow/airflow_deploy
    # Notification service uri used by the scheduler service.
    notification_server_uri: localhost:50052
```

Note:
- You need to specify the database connection string
- We start the notification service in the previous section so we set start_default_notification to false. And the notification_server_uri must match the notification service we started.
- airflow_deploy_path in scheduler config must match the airflow_deploy_path when we start the airflow event-based scheduler.

### Start the aiflow server
You can start the aiflow server with the following command.
```
start_aiflow.sh
```
And you should see "AIFlow server started".
