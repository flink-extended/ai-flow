# Running AIFlow in Docker

This section will show you how to start AIFlow in docker container.

## Pulling Docker Image
Run following command to pull latest AIFlow docker image.
```shell script
docker pull flinkaiflow/flink-ai-flow:latest
```

## Starting AIFlow in Docker
Run following command to enter the docker container in interactive mode.
```shell script
docker run -it -p 8080:8080 -p 8000:8000 flinkaiflow/flink-ai-flow:latest /bin/bash
```

After entering docker container, run following command to start AIFlow.
```shell script
start-all-aiflow-services.sh
```

## Viewing Web Server

Once all servers started, you can visit the AIFlow Web [[http://127.0.0.1:8000](http://127.0.0.1:8000)] with the default username(admin) and password(admin):

![aiflow login ui](../../images/ai_flow_webui.jpg)

Since Apache Airflow is the [Scheduler](../../architecture/overview.md) by default, you can visit the Airflow Web [[http://127.0.0.1:8080](http://127.0.0.1:8080)] 
with the default username(admin) and password(admin) to view the execution of workflows:

![airflow login ui](../../images/airflow_login_ui.png)

## Run An Example

Now you can run following commands to download and run a machine learning project with AIFlow.

```shell
curl -Lf https://github.com/flink-extended/ai-flow/releases/download/release-0.3.0/examples.tar.gz -o /tmp/ai-flow-examples.tar.gz
tar -zxvf /tmp/ai-flow-examples.tar.gz -C /tmp
python /tmp/examples/sklearn_examples/workflows/batch_train_stream_predict/batch_train_stream_predict.py
```

```{note}
You can also cloning [repository](https://github.com/flink-extended/ai-flow/tree/master/examples) with git if download failed.
```

The example shows how to define an entire machine learning workflow through AIFlow. You can view the workflow definition in batch_train_stream_predict.py. The workflow contains four jobs, including sklearn model batch training, batch validation, model pushing and streaming prediction.

You can see the workflow metadata, and the graph of the workflow on the AIFlow web frontend: [http://127.0.0.1:8000](http://127.0.0.1:8000).

![The metadata of the workflow](../../images/sklearn_batch_train_stream_predict_meta.png)

![The graph of the workflow](../../images/sklearn_batch_train_stream_predict_graph.png)

You can click task view to jump to the workflow execution page:
![The execution of the workflow](../../images/sklearn_batch_train_stream_predict_execution.png)

In the above figure, you can see that the model batch training triggers the model validation with the `MODEL_GENERATED` 
event after the sklearn model generated. After passing the model validation, the model pushing is triggered by the `MODEL_VALIDATED` event. The model streaming prediction is triggered by the `MODEL_DEPLOYED` event.

## What’s Next?

For more details about how to write your own workflow, please refer to the [tutorial](../../tutorial_and_examples/tutorial.md) and  [development](../../development/index.md) document.
