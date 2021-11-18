# Deploying Scheduler

In this guide, we demonstrate how to deploy a Scheduler. At present, the default Scheduler is the Airflow scheduler. The
deployment of the Airflow scheduler is as follows:

## Starting Airflow EventBased Scheduler

We use enhanced Airflow as an event-based scheduler and both
[LocalExecutor](https://airflow.apache.org/docs/apache-airflow/stable/executor/local.html) and
[CeleryExecutor](https://airflow.apache.org/docs/apache-airflow/stable/executor/celery.html) are supported. Follow below
steps to initialize environment and start the Airflow scheduler.

### LocalExecutor

1. Prepare the default Airflow configuration. The following script will generate a default Airflow configuration
   file, `airflow.cfg` at the `$AIRFLOW_HOME` directory or `$HOME/airflow` directory if `$AIRFLOW_HOME` is not set.

   ```bash
   init-airflow-env.sh
   ```

   The script will also create an admin user whose username and password are both `admin`. Please refer
   to [Configuration](configuration) and
   [Airflow Configuration Reference](https://airflow.apache.org/docs/apache-airflow/2.0.0/configurations-ref.html) for
   all configurations you can change.

2. Start the Scheduler.

   ```bash
   start-airflow.sh
   ```

   You can check the log of the scheduler and Airflow webserver at `$AIRFLOW_HOME/logs` or `$HOME/airflow/logs`
   directory. `scheduler-*.log` is log of scheduler and `web-*.log` is log of Airflow web server. You can
   visit http://127.0.0.1:8080 to see the Airflow web UI.

### CeleryExecutor

#### Standalone Deployment

1. Set up Celery broker and result backend. `CeleryExecutor` takes advantage of the [Celery](https://docs.celeryproject.org/en/stable/index.html) to
   scale out the number of workers. For this to work, you need to set up a broker and a result backend refer to the exhaustive [Celery documentation](https://docs.celeryproject.org/en/latest/getting-started/backends-and-brokers/index.html).
   
2. Change the Airflow configuration. You need to change your airflow.cfg to point the `executor` parameter to `CeleryExecutor` and provide the necessary related Celery settings.

3. Set up and kick off all Celery workers. Here are some imperative requirements for your workers:
   * Airflow needs to be installed, and the CLI needs to be in the path.
   * Airflow Configuration settings should be homogeneous across the cluster.

   After setting up Celery workers, you can kick off a worker with following command.
   ```
   airflow celery worker
   ```
   To stop a worker running on a machine you can use:
   ```
   airflow celery stop
   ```

4. \[Optional\] Set up Flower.
   [Flower](https://flower.readthedocs.io/en/latest/) is a web based tool for monitoring and administrating Celery clusters, you can start Flower on any
   machine which has the same Airflow Configuration with workers.
   ```shell script
   airflow celery flower
   ```
   You can visit the Flower web on port 5555 to view the celery workers.

5. Start the Scheduler:
   ```
   start-airflow.sh
   ```

#### Deploy with Docker Compose

You can follow this guide to quickly start AIFlow and Scheduler with `CeleryExecutor` within Docker.

```{note}
The Docker Compose below may be not enough to run production-ready Docker Compose AIFlow installation using it.
This is truly quick-start docker-compose for you to get your hands dirty with AIFlow and `CeleryExecutor`.
```

##### Prerequisites

Make sure you have Docker and Docker Compose installed on your workstation,
otherwise please follow these steps to install the tools.

1. Install [Docker Community Edition (CE)](https://docs.docker.com/engine/install/) on your workstation. Depending on the OS, you may need to configure your Docker instance to use at least 4.00 GB of memory for all containers to run properly.
2. Install [Docker Compose](https://docs.docker.com/compose/install/) on your workstation.

Run the following commands to check whether the tools are installed successfully:
```shell script
docker --version
docker-compose --version
```

##### docker-compose.yaml
To deploy AIFlow with `CeleryExecutor` on Docker Compose, you should fetch [docker-compose.yaml](http://raw.githubusercontent.com/flink-extended/ai-flow/master/docker-compose.yaml).

```shell script
curl -LfO http://raw.githubusercontent.com/flink-extended/ai-flow/master/docker-compose.yaml
```

This file contains several service definitions:

* AIFlow servers - AIFlow Server, Notification Server and Scheduler deployed in one container.
* Workers - The workers who execute the tasks given by the Scheduler.
* Redis - The broker that forwards messages from Scheduler to worker.
* Flower -  The [flower app](https://flower.readthedocs.io/en/latest/) for monitoring the environment. It is available at http://localhost:5555.
* MySQL - The database. Only MySQL is supported in distributed mode for now.
* HDFS - The hadoop dfs which is used to store the source code or any resources of your projects.

##### Initializing Environment

This command will help start up database, redis, hdfs and 3 workers and also initialize execution environment of all servers.
It should be executed in the directory that contains docker-compose.yaml you just downloaded.
```shell script
docker-compose up -d --scale airflow-worker=3
```
You can run ```docker ps ``` to check whether all components are started and healthy.

##### Starting Services

Execute following command to start up all services.
```shell script
docker exec ai-flow_aiflow-server_1 bash -c "start-all-aiflow-services.sh"
```
Once all servers started, you can visit the [Flower web](http://127.0.0.1:5555/) to view the celery workers.

##### Running Example
```shell script
docker exec ai-flow_aiflow-server_1 bash -c "python /opt/aiflow/examples/celery/workflows/simple_workflow/simple_workflow.py"
```

(configuration)=

## Configuration

This section shows a list of all Airflow configurations that should be considered. Please refer to
[Airflow Configuration Reference](https://airflow.apache.org/docs/apache-airflow/2.0.0/configurations-ref.html) for all
other configurations.

|Section|Key|Type|Default|Description|
|---|---|---|---|---|
|webserver|notification_sql_alchemy_conn|String|sqlite:///${HOME}/notification_service/ns.db|The notification service db connection.|
|scheduler|notification_server_uri|String|127.0.0.1:50052|The notification server uri used by EventBasedSchedulerJob.|
|scheduler|executor|String|LocalExecutor|The executor class that airflow should use. Choices include ``LocalExecutor``, ``CeleryExecutor``.|
|celery|broker_url|String|redis://redis:6379/0|The Celery broker URL. Celery supports RabbitMQ, Redis and experimentally a sqlalchemy database. Refer to the Celery documentation for more information. This is useful when using ``CeleryExecutor``.|
|celery|result_backend|String|redis://redis:6379/0|The Celery result_backend. This status is used by the scheduler to update the state of the task. The use of a database is highly recommended. This is useful when using ``CeleryExecutor``.|
|celery|worker_log_server_port|Integer|8793|The port on which the logs are served. It needs to be unused, and open visible from the main web server to connect into the workers. This is useful when using ``CeleryExecutor``.|
