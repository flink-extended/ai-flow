# Tutorial

This tutorial will show you how to create and run a workflow using AIFlow SDK and walk you through the fundamental AIFlow concepts and their usage.

## Creating a workflow

(target)=

### Target

In the tutorial, we will write a simple machine learning workflow to train a KNN model using iris training dataset and verify the effectiveness of the model. 

Furthermore, in this workflow, the training job will be a periodical batch job using scikit-learn library. 
Once the batch training job finishes, we will start a validation job to validate the correctness and generalization ability of the generated model. 
Finally, when a model is validated, we will start a Flink job to utilize the model to do prediction and save prediction results to a local file.

### Prepare a Project

Before creating the workflow, we should prepare a project whose directory structure is as follows:

```
tutorial_project/
        |- workflows/
           |- tutorial_workflow/
              |- tutorial_workflow.py 
              |- tutorial_workflow.yaml 
        |- dependencies/
            |-python 
            |-jar
        |- resources/
        └─ project.yaml
```

`tutorial_project` is the root directory of the project and `workflows` is used to save codes and config files of workflows in this project. 

The `dependecies` directory is used to save python/jar dependencies that will be used by our workflow.

The `resources` directory is for saving all other files(e.g., config files) that will be used by the project.

The `project.yaml` is the project config file. 

#### project.yaml

Here is an example of the project.yaml for tutorial project.

```yaml
project_name: tutorial_project
server_uri: localhost:50051
notification_server_uri: localhost:50052
blob:
  blob_manager_class: ai_flow_plugins.blob_manager_plugins.local_blob_manager.LocalBlobManager
```

In `project_name`, we define the project's name, which will be the default namespace of workflows in this project as well. 

```{note}
Namespace in AIFlow is used for isolation. Each workflow can only send events to its own namespace while it can listen on multiple namespaces. 
The reason for enabling listening on multiple namespaces is that the workflow could be triggered by external events from Notification Server.
``` 
For `server_uri`,  they tell where the AIFlow Server is running on.

For `notification_server_uri`,  they tell where the Notification Server is running on.

Then, we configure the `blob` property which specifies where the workflow code will be updated when submitting. 
It also tells the AIFlow Server where and how to download the workflow code.

Here we choose to use `LocalBlobManager` and as a result, the AIFlow Server will download the workflow code locally. 
Please note that `LocalBlobManager` can only work when you submit your workflow on the same machine as the AIFlow server.

We currently also provide other implementations of `BlobManager` like `OssBlobManager` and `HDFSBlobManager` which allows users to **submit their workflow to a remote AIFlow Server**.

* `OssBlobManager`

```yaml
project_name: tutorial_project
server_uri: [Remote AIFlow server uri]
notification_server_uri: [Remote Notification server uri]
blob:
  blob_manager_class: ai_flow_plugins.blob_manager_plugins.oss_blob_manager.OssBlobManager
  blob_manager_config:
        access_key_id: [The id of the access key]
        access_key_secret: [The secret of the access key]
        endpoint: [Access domain name or CNAME]
        bucket: [The name of the bucket]
        root_directory: [The upload directory of the bucket]
```

* `HDFSBlobManager`

```yaml
project_name: tutorial_project
server_uri: [Remote AIFlow server uri]
notification_server_uri: [Remote Notification server uri]
blob:
  blob_manager_class: ai_flow_plugins.blob_manager_plugins.hdfs_blob_manager.HDFSBlobManager
  blob_manager_config:
        hdfs_url: [Hostname or IP address of HDFS namenode, prefixed with protocol, followed by WebHDFS port on namenode]
        hdfs_user: [User default. Defaults to the current user's (as determined by `whoami`)]
        root_directory: [The upload directory of the bucket]
```

* `S3BlobManager`

```yaml
project_name: tutorial_project
server_uri: [Remote AIFlow server uri]
notification_server_uri: [Remote Notification server uri]
blob:
  blob_manager_class: ai_flow_plugins.blob_manager_plugins.s3_blob_manager.S3BlobManager
  blob_manager_config:
        service_name: [The name of a service, e.g. 's3' or 'ec2']
        region_name: [The name of the region associated with the client]
        api_version: [The API version to use]
        use_ssl: [Whether or not to use SSL]
        verify: [Whether or not to verify SSL certificates]
        endpoint_url: [The complete URL to use for the constructed client]
        access_key_id: [The access key for your AWS account]
        secret_access_key: [The secret key for your AWS account]
        session_token: [The session key for your AWS account]
        config: [Advanced client configuration options]
        bucket_name: [The S3 bucket name]
```

### Prepare a Workflow

#### tutorial_workflow
We will create a `tutorial_workflow` directory for our workflow. 
In the `tutorial_workflow.py`, we will add our actual codes for defining the workflow and `tutorial_workflow.yaml` includes some configs of our workflow.

```{note}
The names of 'tutorial_workflow.py' and 'tutorial_workflow.yaml' must be same as the name of 'tutorial_workflow' directory.
```

#### tutorial_workflow.yaml 

Next, we will introduce how to write the workflow configuration yaml file.

```yaml
train:
  job_type: python
  periodic_config:
    interval: '0,0,0,60' # The train job will be executed every 60s
  # properties:
  #  train_param_key: train_param_val

validate:
  job_type: python

predict:
  job_type: flink
  properties:
    run_mode: cluster
    flink_run_args: #The flink run command args(-pym, -pyexec etc.). It's type is List.
      - -pyexec
      - /path/to/bin/python # path to your python3.7 executable path
```

In the tutorial_workflow.yaml, we define the properties of each job. 

For `train` job, its job type is `python`, which means the user defined logic in this job will be executed using `python`. Besides, we set the `periodic_config` to be `interval: '0,0,0,60'` which means the job will be executed every 60s. The `properties` option which represents the additional properties of the job config can also be configured. The `properties` in the job config can be obtained through **`af.current_workflow_config().job_configs['job_name'].properties`**  in the `process` method in the user-defined `PythonProcessor` implementation.

For `validate` job, we only config its job type to be `python`.

For `predict` job, we set its job type to be `flink`, which means this job is a flink job. In addition, to use flink, we need to set some flink-specific properties including `run_mode` (cluster or local) and `flink_run_args`. For the `flink_run_args`, we follow the list format of `yaml` to add the args such as the `-pyexec`.

### Define a Workflow

Now, let's start to define a workflow described in [Target](target) section using the AIFlow SDK.

#### Import Modules

In AIFlow, a workflow is just a Python script. Let’s create `tutorial_workflow.py` and start by importing the libraries we will need.

```python
import os

# Entry of accessing AIFlow API
import ai_flow as af

# Enum class for marking different stages of our workflow
from ai_flow.model_center.entity.model_version_stage import ModelVersionEventType

# Util functions provided by ai_flow
from ai_flow.util.path_util import get_file_dir

# User-defined processors; we will introduce them in tutorial_processors.py
from tutorial_processors import DatasetReader, ModelTrainer, ValidateDatasetReader, ModelValidator, Source, Sink, \
    Predictor

# Declare the location of dataset
DATASET_URI = os.path.abspath(os.path.join(__file__, "../../../")) + '/resources/iris_{}.csv'

```

#### Define a Training Job

In our design, the workflow in AIFlow is a DAG(Directed Acyclic Graph) or to be more specific, it is a [AIGraph](https://github.com/flink-extended/ai-flow/blob/master/ai_flow/ai_graph/ai_graph.py#L28). Each node in the graph is an [AINode](https://github.com/flink-extended/ai-flow/blob/master/ai_flow/ai_graph/ai_node.py#L29), which contains a processor. Users should write their custom logic in the processor. 

In the AIGraph, nodes are connected by 2 types of edges. The first one is named as `DataEdge` which means the destination node depends on the output of the source node. The other is `ControlEdge` which means the destination node depends on the control conditions from source node. We will dive deeper into this kind of edges later.

For now, let's concentrate on the set of AINodes connected by only data edges. Such a set of nodes and data edges between them constitutes a sub-graph. This sub-graph, together with the predefined job config in workflow config yaml, is mapped to a Job by AIFlow framework.

So, to summarize, each AIFlow job is made up of a job config, some AINodes and the data edges between those nodes. 

These concepts seem to be a little difficult, but do not worry. Let's look at some code snippets, and you will find it pretty easy to define a job with provided API of AIFlow.

In the following codes, we define a training job of our workflow:
```python
    artifact_prefix = af.current_project_config().get_project_name() + "."
    # Training of model
    with af.job_config('train'):
        # Register metadata of training data(dataset), `uri` refers to the file path
        train_dataset = af.register_dataset(name=artifact_prefix + 'train_dataset',
                                            uri=DATASET_URI.format('train'))
        # Read data from the registered dataset with user-defined read_dataset_processor
        train_read_dataset = af.read_dataset(dataset_info=train_dataset,
                                             read_dataset_processor=DatasetReader())

        # Register model metadata
        train_model = af.register_model(model_name=artifact_prefix + 'KNN',
                                        model_desc='KNN model')
        # Train the model with user-defined training_processor
        train_channel = af.train(input=[train_read_dataset],
                                 training_processor=ModelTrainer(),
                                 model_info=train_model)
```

In the above codes, methods like `register_dataset` and `register_model` are just used to save some metadata(e.g., the name of the model or the uri of the dataset) into the database. The return value of these methods are some metadata objects(e.g. `DatasetMeta` or `ModelMeta`), which can be used to query metadata or serve as parameters of other methods.

On the other hand, `read_dataset()` and `train()` are of another type. We call them `Operators` as they have some specific semantics and will create corresponding `AINodes`. Then, how do we define the data dependency of those newly created nodes? We just put the output of `read_dataset` method into the `input` arg of `train()` method. Such codes imply input of the training node created by`train()` is the output of the node created by `read_dataset()` .  The return values of methods like `train()` are `Channel` or list of `Channel`s.

In AIFlow, `Channel` represents the output of AINodes. More vividly, `Channel` is one end of the `DataEdge`. The following picture shows the relation among `AINodes`, `DataEdges` and `Channels`:

![Alt text](../images/tutorial/channels.png)

In the example, AINode N0 has 3 outputs(i.e., 3 channels whose source node is N0). We can make N1 accepts the c0 and c1 channels and N2 accepts c1 and c2 channels. Accordingly, there are 4 DataEdges in all. With such design, we can manipulate the data dependencies more flexibly and reuse the data easier.

Currently, the only puzzle left is how to implement the processors including `DatasetReader()` and `ModelTrainer()`. We will introduce them later in [Implement Custom Processors](implement-custom-processors) section. Next, let's pay attention to defining the Validation and Prediction jobs.

#### Define a Validation Job and a Prediction Job

Here we define the other two jobs of our workflow. They are pretty similar to what we have done in defining the training job.

```python
		# Validation of model
    with af.job_config('validate'):
        # Read validation dataset
        validate_dataset = af.register_dataset(name=artifact_prefix + 'validate_dataset',
                                               uri=DATASET_URI.format('test'))
        # Validate model before it is used to predict
        validate_read_dataset = af.read_dataset(dataset_info=validate_dataset,
                                                read_dataset_processor=ValidateDatasetReader())
        validate_artifact_name = artifact_prefix + 'validate_artifact'
        validate_artifact = af.register_artifact(name=validate_artifact_name,
                                                 uri=get_file_dir(__file__) + '/validate_result')
        validate_channel = af.model_validate(input=[validate_read_dataset],
                                             model_info=train_model,
                                             model_validation_processor=ModelValidator(validate_artifact_name))

    # Prediction(Inference) using flink
    with af.job_config('predict'):
        # Read test data and do prediction
        predict_dataset = af.register_dataset(name=artifact_prefix + 'predict_dataset',
                                              uri=DATASET_URI.format('test'))
        predict_read_dataset = af.read_dataset(dataset_info=predict_dataset,
                                               read_dataset_processor=Source())
        predict_channel = af.predict(input=[predict_read_dataset],
                                     model_info=train_model,
                                     prediction_processor=Predictor())
        # Save prediction result
        write_dataset = af.register_dataset(name=artifact_prefix + 'write_dataset',
                                            uri=get_file_dir(__file__) + '/predict_result.csv')
        af.write_dataset(input=predict_channel,
                         dataset_info=write_dataset,
                         write_dataset_processor=Sink())

```

In above codes, we use 3 new predefined operators by AIFlow: `model_validate()` , `predict()`, `write_dataset()`. 

In addition, in AIFlow, if they don't find the operators needed, users can also define their own operators with the `user_define_operation()` API.

#### Define the Relation between Jobs

We now have defined 3 jobs. Each job has some nodes connected by `DataEdge`s. Then we will need to define relations between jobs to make sure our workflow is scheduled and run correctly. As we have mentioned in [Target](target) section, the training job will run periodically and once the training finishes, the validation job should be started to validate the latest generated model. If there is a model passes the validation and get deployed, we should (re)start the downstream prediction job to get better inference.

After reviewing above description, we find that some upstream jobs control the downstream jobs. For instance, the training job controls the (re)start of validation job. We keep using AIGraph abstraction to depicts these control relations. But at this time, each AINode in this new AIGraph is a job. Edges to connect these job nodes are named as `ControlEdge`. We also call such control relation as *control dependencies*.

In AIFlow, we implement control dependencies via *Events*. That is, the upstream job can send specific events to downstream jobs and downstream jobs will take actions due to the events and rules defined by users.

```python
		# Define relation graph connected by control edge: train -> validate -> predict
    af.action_on_model_version_event(job_name='validate',
                                     model_version_event_type=ModelVersionEventType.MODEL_GENERATED,
                                     model_name=train_model.name)
    af.action_on_model_version_event(job_name='predict',
                                     model_version_event_type=ModelVersionEventType.MODEL_VALIDATED,
                                     model_name=train_model.name)
```

In above codes, the first `ControlEdge` we defined is that the `validate` job (Note, this job name is defined in the yaml file of workflow configs) will be restarted(the default action) when there is a `MODEL_GENERATED` event. The second  `ControlEdge` we defined is that the `predict` job will be restarted when there is a `MODEL_VALIDATED` event. 

Besides, the well-defined out-of-box API for managing machine learning jobs, AIFlow exposes the most flexible API `action_on_events()` to allow users write their own control dependencies.

## Manage a Workflow

We have finished the definition of the workflow. Now we need to submit and run it.

```python
def run_workflow():
    # Init project
    af.init_ai_flow_context()

    artifact_prefix = af.current_project_config().get_project_name() + "."
    # Training of model
    with af.job_config('train'):
        ...
    # Validation of model
    with af.job_config('validate'):
        ...
    # Prediction(Inference) using flink
    with af.job_config('predict'):
        ...

    # Define relation graph connected by control edge: train -> validate -> predict
    af.action_on_model_version_event(job_name='validate',
                                     model_version_event_type=ModelVersionEventType.MODEL_GENERATED,
                                     model_name=train_model.name)
    af.action_on_model_version_event(job_name='predict',
                                     model_version_event_type=ModelVersionEventType.MODEL_VALIDATED,
                                     model_name=train_model.name)
    # Submit and run workflow
    af.workflow_operation.submit_workflow(af.current_workflow_config().workflow_name)
    af.workflow_operation.start_new_workflow_execution(af.current_workflow_config().workflow_name)

if __name__ == '__main__':
    run_workflow()
```

Above codes show the basic use of workflow administration API. You may notice that our naming convention of workflow management API seems inconsistent: `submit_workflow()` and `start_new_workflow_execution()`. 

In fact, in our design, `Workflow` defines the execution logic of a set of jobs together with control edges among them. But after definition, the workflow will not be run. Instead, the workflow will be scheduled by the scheduler(e.g., Airflow scheduler) after calling `start_new_workflow_execution()`. The execution entity of workflow is named as `WorkflowExecution`, which is created by the scheduler.

(implement-custom-processors)=

## Implement Processors

As we have mentioned, users need to write their own logic in processors for each job. Currently, AIFlow provides `bash`, `python` and `flink` processors.

The following codes are the `DatasetReader` processor whose type is `python`:

```python
EXAMPLE_COLUMNS = ['sl', 'sw', 'pl', 'pw', 'type']

class DatasetReader(PythonProcessor):

    def process(self, execution_context: ExecutionContext, input_list: List) -> List:
        """
        Read dataset using pandas
        """
        # Gets the registered dataset meta info
        dataset_meta: af.DatasetMeta = execution_context.config.get('dataset')
        # Read the file using pandas
        train_data = pd.read_csv(dataset_meta.uri, header=0, names=EXAMPLE_COLUMNS)
        # Prepare dataset
        y_train = train_data.pop(EXAMPLE_COLUMNS[4])
        return [[train_data.values, y_train.values]]
```

As you can see, it is just a python program using pandas library without any mystery.

Next, we show an example of Flink processors:

```python 
class Predictor(flink.FlinkPythonProcessor):
    def __init__(self):
        super().__init__()
        self.model_name = None

    def setup(self, execution_context: flink.ExecutionContext):
        self.model_name = execution_context.config['model_info'].name

    def process(self, execution_context: flink.ExecutionContext, input_list: List[Table] = None) -> List[Table]:
        """
        Use pyflink udf to do prediction
        """
        model_meta = af.get_deployed_model_version(self.model_name)
        model_path = model_meta.model_path
        clf = load(model_path)

        class Predict(ScalarFunction):
            def eval(self, sl, sw, pl, pw):
                records = [[sl, sw, pl, pw]]
                df = pd.DataFrame.from_records(records, columns=['sl', 'sw', 'pl', 'pw'])
                return clf.predict(df)[0]

        execution_context.table_env.register_function('mypred',
                                                      udf(f=Predict(),
                                                          input_types=[DataTypes.FLOAT(), DataTypes.FLOAT(),
                                                                       DataTypes.FLOAT(), DataTypes.FLOAT()],
                                                          result_type=DataTypes.FLOAT()))
        return [input_list[0].select("mypred(sl,sw,pl,pw)")]
```

It is written in Pyflink for convenience and Flink Java Processor is also supported. And to run flink job without bugs, please make sure the properties for running a Flink job is set properly in `tutorial_workflow.yaml` according to your local environment. 

Note, if you use some special dependencies and choose to submit the workflow to a remote environment for execution, you should put your dependencies in the `tutorial_project/dependencies` folder and refer them properly. That's because AIFlow will upload the whole project directory to remote for execution and users need to make sure in the remote env, the python processors can run correctly.

## Run a Workflow

Now we have finished the introduction of how to write a workflow. For the whole codes, please go to check [tutorial_project](https://github.com/flink-extended/ai-flow/tree/master/examples/tutorial_project) directory. After configuring the yaml file according to your own environment, it is time to run the workflow. 

Before running, please make sure you have installed AIFlow and started AIFlow Server, Notification Server and Scheduler correctly according to the QuickStart document.

Then, type following commands in your terminal:
```bash
cd ai-flow/examples/tutorial_project
python workflows/tutorial_workflow/tutorial_workflow.py
```

Once the bash command returns(it should take no longer than 1 minute), go to check the Airflow WebUI to see if the workflow is submitted successfully. If it is success, wait a minute(because we set the training job to be executed every 1 minute in the config file) then you can see the graph like this:

![Alt text](../images/tutorial/success_workflow.png)

You can view the prediction output under in the file `examples/tutorial_project/workflows/tutorial_workflow/predict_result.csv` as well.

If you find any job fails, you can go to check logs under directory like `examples/tutorial_project/temp/tutorial_workflow/$jobname/202107xxxxx/logs`. The log files will give you the error information in detail. Also, checking the log in the Airflow WebUI is also a good choice.

## Conclusion

Congratulations! You have been equipped with necessary knowledge to write your own workflow. For further reading, you can check our [Overview](../architecture/overview.md), [API](../api/index.rst) and [Examples](https://github.com/flink-extended/ai-flow/tree/master/examples/). 
