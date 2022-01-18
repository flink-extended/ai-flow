# Quickstart

The Quickstart will show you how to start AIFlow, you can choose to start AIFlow either on local workstation or in Docker. 

## Running AIFlow Locally
### Installing AIFlow


### Start AIFlow 

AIFlow contains three long-running servers, AIFlow Server, Notification server and Scheduler(Apache Airflow by default).
You can start all servers with a single script `start-all-aiflow-services.sh` as below:.

```shell
start-all-aiflow-services.sh
```

It will take a few minutes to start all servers for the first time. Once all servers have started, you will get the output like:

```text
Starting Notification Server
...
...
All services have been started!
```

### View Web Server

Once all servers started, you can visit the AIFlow Web [[http://127.0.0.1:8000](http://127.0.0.1:8000)] with the default username(admin) and password(admin):

![aiflow login ui](../images/ai_flow_webui.jpg)

Since Apache Airflow is the [Scheduler](../architecture/overview.md) by default, you can visit the Airflow Web [[http://127.0.0.1:8080](http://127.0.0.1:8080)] 
with the default username(admin) and password(admin) to view the execution of workflows:

![airflow login ui](../images/airflow_login_ui.png)

### What’s Next?
Now you can head to the [Example](./run_example.md) section to run a machine learning workflow with AIFlow.

## Running AIFlow In Docker

### Start AIFlow
You can also start AIFlow in Docker if you don't want to install AIFlow locally. 
Please run following commands to enter the docker container in interactive mode and start servers inner docker. 

```shell script
docker run -it -p 8080:8080 -p 8000:8000 flinkaiflow/flink-ai-flow:latest /bin/bash
start-all-aiflow-services.sh
```

### View Web Server

Once all servers started, you can visit the AIFlow Web [[http://127.0.0.1:8000](http://127.0.0.1:8000)] with the default username(admin) and password(admin):

![aiflow login ui](../images/ai_flow_webui.jpg)

Since Apache Airflow is the [Scheduler](../architecture/overview.md) by default, you can visit the Airflow Web [[http://127.0.0.1:8080](http://127.0.0.1:8080)] 
with the default username(admin) and password(admin) to view the execution of workflows:

![airflow login ui](../images/airflow_login_ui.png)

### What’s Next?
Now you can head to the [Example](./run_example.md) section to run a machine learning workflow with AIFlow.
