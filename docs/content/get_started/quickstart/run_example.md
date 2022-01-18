# Machine Learning with AIFlow

We have prepared some [examples](https://github.com/alibaba/flink-ai-extended/releases/download/ai-flow-release-0.2.2/ai-flow-examples.tar.gz) to get started. 
You can run following commands to download and run the sklearn example.

```shell
curl -Lf https://github.com/flink-extended/ai-flow/releases/download/release-0.3.0/examples.tar.gz -o /tmp/ai-flow-examples.tar.gz
tar -zxvf /tmp/ai-flow-examples.tar.gz -C /tmp
python /tmp/examples/sklearn_examples/workflows/batch_train_stream_predict/batch_train_stream_predict.py
```

The example shows how to define an entire machine learning workflow through AIFlow. 
You can view the workflow definition in batch_train_stream_predict.py. 
The workflow contains four jobs, including sklearn model batch training, batch validation, model pushing and streaming prediction.

You can see the workflow metadata, and the graph of the workflow on the AIFlow web frontend: [http://127.0.0.1:8000](http://127.0.0.1:8000).

![The metadata of the workflow](../../images/sklearn_batch_train_stream_predict_meta.png)

![The graph of the workflow](../../images/sklearn_batch_train_stream_predict_graph.png)

You can click task view to jump to the workflow execution page:
![The execution of the workflow](../../images/sklearn_batch_train_stream_predict_execution.png)

In the above figure, you can see that the model batch training triggers the model validation with the `MODEL_GENERATED` 
event after the sklearn model generated. After passing the model validation, 
the model pushing is triggered by the `MODEL_VALIDATED` event. 
The model streaming prediction is triggered by the `MODEL_DEPLOYED` event.

For more details about how to write your workflow, please refer to the [Tutorial](../workflow_development/tutorial.md) document.
