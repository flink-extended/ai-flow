# Running AIFlow locally

This section will show you how to install and start AIFlow on your local workstation.

## Installing AIFlow
You can install AIFlow by running:
```shell script
pip install ai-flow
```

```{note}
Currently AIFlow only supports python3.7, please make sure your python version meets the requirement.
Meanwhile, we strongly recommend using [virtualenv](https://virtualenv.pypa.io/en/latest/index.html) or other similar tools for an isolated Python environment.
```shell
pip install virtualenv
virtualenv venv_for_aiflow --python=python3.7
source venv_for_aiflow/bin/activate
```


## Starting AIFlow 

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
```{note}
You may run into issues caused by different operating systems or versions, 
please refer to [Troubleshooting](./troubleshooting.md) section to get solutions.
```
## Viewing Web Server

Once all servers started, you can visit the AIFlow Web [[http://127.0.0.1:8000](http://127.0.0.1:8000)] with the default username(admin) and password(admin):

![aiflow login ui](../../images/ai_flow_webui.jpg)

Since Apache Airflow is the [Scheduler](../architecture/overview.md) by default, you can visit the Airflow Web [[http://127.0.0.1:8080](http://127.0.0.1:8080)] 
with the default username(admin) and password(admin) to view the execution of workflows:

![airflow login ui](../../images/airflow_login_ui.png)

## What’s Next?
Now you can head to the [Example](./run_example.md) section to run a machine learning workflow with AIFlow.
