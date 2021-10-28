# Quickstart

The Quickstart will show you how to start AI Flow and help you get started with an example in AI Flow.

- [Prepare Database](#prepare-database)
  * [Install and Start MySQL Server](#install-and-start-mysql-server)
  * [Create User and Database](#create-user-and-database)
- [Run AI Flow locally](#run-ai-flow-locally)
  * [Install AI Flow](#install-ai-flow)
  * [Start Servers](#start-servers)
- [Run AI Flow in Docker](#run-ai-flow-in-docker)
  * [Build Image](#build-image)
  * [Start Servers In Docker](#start-servers-in-docker)
- [Run Example](#run-example)
- [Stop Servers](#stop-servers)
- [Troubleshooting](#troubleshooting)

## Prepare Database

Currently only MySQL is supported to be used as storage backend.

### Install and Start MySQL Server

If you've got a started MySQL Server somewhere, please skip this section.

#### Locally

Please refer to [MySQL Installation](https://dev.mysql.com/doc/refman/8.0/en/installing.html)  to install MySQL locally.

#### Docker

```
docker run --name aiflow-mysql -e MYSQL_ROOT_PASSWORD=root -d -p3306:3306 mysql:8
```

### Create User and Database

```
# create default user and password
CREATE USER 'aiflow' IDENTIFIED BY 'aiflow';
GRANT ALL PRIVILEGES ON airflow.* TO 'aiflow';

# create database
CREATE DATABASE aiflow CHARACTER SET utf8 COLLATE utf8_unicode_ci;
```

## Run AI Flow locally

### Install AI Flow

Please refer to [[Installation]] for the installation guide.

### Start Servers

As described in [[Design]],  AI Flow contains three long running services, Notification service, AI Flow Server and Scheduler service(Apache Airflow by default), you could start all services with a single scripts `start-all-aiflow-services.sh` as below. The mysql database that you prepared during [Prepare Database](#prepare-database) should be passed as parameter to store metadata.

```shell
start-all-aiflow-services.sh mysql://aiflow:aiflow@127.0.0.1/aiflow
```

It will take a few minutes the first time you start. Once finished you will get the output like:

```text
~/airflow/airflow.cfg does not exist creating one.
DB: mysql://aiflow:***@127.0.0.1/aiflow
Initialization done
Try to create admin airflow user
Admin user admin created
Starting AIFlow Server
AIFlow Server started
Starting AIFlow Web
AIFlow Web started
...
Airflow deploy path: /root/aiflow/airflow_deploy
Visit http://127.0.0.1:8080/ to access the airflow web server.
```

You may have noticed that some logs are related to Apache Airflow, that is because Apache Airflow is the default [[Scheduler Service|https://github.com/flink-extended/ai-flow/wiki/Design#scheduler-service]]. To check the scheduler started successfully, you can visit the AIFlow Web [[http://127.0.0.1:8000](http://127.0.0.1:8000)] and Airflow Web [[http://127.0.0.1:8080](http://127.0.0.1:8080)] with the default user name(admin) and password(admin).

![Alt text](../images/ai_flow_webui.jpg)

## Run AI Flow in Docker

### Start Servers In Docker

Now you have an image named ai-flow with tag v1. You can run image with following command.

```shell
docker run -it  -p 8080:8080 flinkaiflow/flink-ai-flow:0.2.0 /bin/bash
```

After that you can start servers within container same as [Start Servers Locally](#start-servers).

## Run Example

We have prepared some examples to get started, you can download from [release source](https://github.com/alibaba/flink-ai-extended/releases/download/ai-flow-release-0.1.0/ai-flow-examples.tar.gz). Once downloaded, you can run following commands to submit a simple workflow.

```shell
wget https://github.com/alibaba/flink-ai-extended/releases/download/ai-flow-release-0.1.0/ai-flow-examples.tar.gz -O /tmp/ai-flow-examples.tar.gz
tar -zxvf /tmp/ai-flow-examples.tar.gz -C /tmp
python /tmp/examples/demo/workflows/simple_workflow/simple_workflow.py
```

You can view workflow definition in simple_workflow.py. There are 2 jobs in workflow, the first one runs `echo hello_1` once the workflow submitted and the second one runs `echo hello_2` after the first one finished.

You can see the metadata and the graph of the workflow on the AIFlow Web [[http://127.0.0.1:8000](http://127.0.0.1:8000)].

![The metadata of the simple_workflow](../images/simple_workflow_metadata.jpg)

![The graph of the simple_workflow](../images/simple_workflow_graph.jpg)

You can see your workflow and the outputs of each job on the Airflow Web [[http://127.0.0.1:8080](http://127.0.0.1:8080)].

For more details about how to write your own workflow, please refer to [[Tutorial|Tutorial]].

## Stop Servers

Run following command to stop notification server, Airflow Server and AI Flow Server:

```shell
stop-all-aiflow-services.sh
```

## Troubleshooting

### 1. Can't connect to MySQL server in docker

Detail message: `(2002, "Can't connect to MySQL server on '127.0.0.1' (115)")`

If your MySQL server is started at your local machine, your need to replace `mysql://user:password@127.0.0.1/airflow` with `mysql://user:password@host.docker.internal/airflow`.

### 2. caching_sha2_password could not be loaded

Due to MySQL's [document](https://dev.mysql.com/doc/refman/8.0/en/upgrading-from-previous-series.html), caching_sha2_password is the the default authentication plugin since MySQL 8.0. If you meet this problem 
when launching docker, you can fix it by changing it back to naive version. To do that, in your MySQL server on host machine, type following command:

```SQL
ALTER USER 'username'@'%' IDENTIFIED WITH mysql_native_password BY 'password';
ALTER USER 'username'@'localhost' IDENTIFIED WITH mysql_native_password BY 'password';
FLUSH PRIVILEGES; 
```
Then restart MySQL service and the docker image.

### 3. pytz.exceptions.UnknownTimeZoneError: 'Can not find any timezone configuration'

It is a common problem in Ubantu, the solution is set the locale environment variable correctly, e.g.
```
export TZ=America/Indiana/Indianapolis
```

### 4. ValueError: unknown locale: UTF-8

You may meet this error with earlier version of Python, please set the environment variables like below.

```text
export LANGUAGE=en_US.UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export LC_CTYPE=en_US.UTF-8
export LC_MESSAGES=en_US.UTF-8
```
