# Tutorial

This tutorial will show you how to create and run a workflow using AIFlow SDK and walk you through the fundamental AIFlow concepts and their usage.
In the tutorial, we will write a simple machine learning workflow to train a Logistic Regression model and verify the effectiveness of the model using MNIST dataset.

## Example Workflow definition

```python
import logging
import os
import shutil
import time
import numpy as np

from typing import List
from joblib import dump, load

from sklearn.utils import check_random_state
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import LogisticRegression

from ai_flow import ops
from ai_flow.model.action import TaskAction
from ai_flow.operators.python import PythonOperator
from ai_flow.model.workflow import Workflow
from ai_flow.notification.notification_client import AIFlowNotificationClient, ListenerProcessor, Event


NOTIFICATION_SERVER_URI = "localhost:50052"

current_dir = os.path.dirname(__file__)
dataset_path = os.path.join(current_dir, 'dataset', 'mnist_{}.npz')
working_dir = os.path.join(current_dir, 'tmp')

trained_model_dir = os.path.join(working_dir, 'trained_models')
validated_model_dir = os.path.join(working_dir, 'validated_models')
deployed_model_dir = os.path.join(working_dir, 'deployed_models')


def _prepare_working_dir():
    for path in [trained_model_dir, validated_model_dir, deployed_model_dir]:
        if not os.path.isdir(path):
            os.makedirs(path)


def _get_latest_model(model_dir) -> str:
    file_list = os.listdir(model_dir)
    if file_list is None or len(file_list) == 0:
        return None
    else:
        file_list.sort(reverse=True)
        return os.path.join(model_dir, file_list[0])


def _preprocess_data(dataset_uri):
    with np.load(dataset_uri) as f:
        x_data, y_data = f['x_train'], f['y_train']

    random_state = check_random_state(0)
    permutation = random_state.permutation(x_data.shape[0])
    x_train = x_data[permutation]
    y_train = y_data[permutation]

    reshaped_x_train = x_train.reshape((x_train.shape[0], -1))
    scaler_x_train = StandardScaler().fit_transform(reshaped_x_train)
    return scaler_x_train, y_train


def preprocess():
    _prepare_working_dir()
    train_dataset = dataset_path.format('train')
    try:
        event_sender = AIFlowNotificationClient(NOTIFICATION_SERVER_URI)
        while True:
            x_train, y_train = _preprocess_data(train_dataset)
            np.save(os.path.join(working_dir, f'x_train'), x_train)
            np.save(os.path.join(working_dir, f'y_train'), y_train)
            event_sender.send_event(key="data_prepared", value=None)
            time.sleep(30)
    finally:
        event_sender.close()


def train():
    """
    See also:
        https://scikit-learn.org/stable/auto_examples/linear_model/plot_sparse_logistic_regression_mnist.html
    """
    _prepare_working_dir()
    clf = LogisticRegression(C=50. / 5000, penalty='l1', solver='saga', tol=0.1)
    x_train = np.load(os.path.join(working_dir, f'x_train.npy'))
    y_train = np.load(os.path.join(working_dir, f'y_train.npy'))
    clf.fit(x_train, y_train)
    model_path = os.path.join(trained_model_dir, time.strftime("%Y%m%d%H%M%S", time.localtime()))
    dump(clf, model_path)


def validate():
    _prepare_working_dir()

    validate_dataset = dataset_path.format('evaluate')
    x_validate, y_validate = _preprocess_data(validate_dataset)

    to_be_validated = _get_latest_model(trained_model_dir)
    clf = load(to_be_validated)
    scores = cross_val_score(clf, x_validate, y_validate, scoring='precision_macro')
    try:
        event_sender = AIFlowNotificationClient(NOTIFICATION_SERVER_URI)
        deployed_model = _get_latest_model(deployed_model_dir)
        if deployed_model is None:
            logging.info(f"Generate the 1st model with score: {scores}")
            shutil.copy(to_be_validated, validated_model_dir)
            event_sender.send_event(key="model_validated", value=None)
        else:
            deployed_clf = load(deployed_model)
            old_scores = cross_val_score(deployed_clf, x_validate, y_validate, scoring='precision_macro')
            if np.mean(scores) > np.mean(old_scores):
                logging.info(f"A new model with score: {scores} passes validation")
                shutil.copy(to_be_validated, validated_model_dir)
                event_sender.send_event(key="model_validated", value=None)
            else:
                logging.info(f"New generated model with score: {scores} is worse "
                             f"than the previous: {old_scores}, ignored.")
    finally:
        event_sender.close()


def deploy():
    _prepare_working_dir()
    to_be_deployed = _get_latest_model(validated_model_dir)
    deploy_model_path = shutil.copy(to_be_deployed, deployed_model_dir)
    try:
        event_sender = AIFlowNotificationClient(NOTIFICATION_SERVER_URI)
        event_sender.send_event(key="model_deployed", value=deploy_model_path)
    finally:
        event_sender.close()


class ModelLoader(ListenerProcessor):
    def __init__(self):
        self.current_model = None
        logging.info("Waiting for the first model deployed...")

    def process(self, events: List[Event]):
        for e in events:
            self.current_model = e.value


def predict():
    _prepare_working_dir()
    predict_dataset = dataset_path.format('predict')
    result_path = os.path.join(working_dir, 'predict_result')
    x_predict, _ = _preprocess_data(predict_dataset)

    model_loader = ModelLoader()
    current_model = model_loader.current_model
    try:
        event_listener = AIFlowNotificationClient(NOTIFICATION_SERVER_URI)
        event_listener.register_listener(listener_processor=model_loader,
                                         event_keys=["model_deployed", ])
        while True:
            if current_model != model_loader.current_model:
                current_model = model_loader.current_model
                logging.info(f"Predicting with new model: {current_model}")
                clf = load(current_model)
                result = clf.predict(x_predict)
                with open(result_path, 'a') as f:
                    f.write(f'model [{current_model}] predict result: {result}\n')
            time.sleep(5)
    finally:
        event_listener.close()


with Workflow(name="online_machine_learning") as workflow:

    preprocess_task = PythonOperator(name="pre_processing",
                                     python_callable=preprocess)

    train_task = PythonOperator(name="training",
                                python_callable=train)

    validate_task = PythonOperator(name="validating",
                                   python_callable=validate)

    deploy_task = PythonOperator(name="deploying",
                                 python_callable=deploy)

    predict_task = PythonOperator(name="predicting",
                                  python_callable=predict)

    train_task.action_on_event_received(action=TaskAction.START, event_key="data_prepared")

    validate_task.start_after(train_task)

    deploy_task.action_on_event_received(action=TaskAction.START, event_key="model_validated")
```
The above Python script declares a Workflow that consists of 5 batch or streaming tasks related to machine learning. The general logic of the workflow is as follows:
1. A `pre_processing` task continuously generates training data and do some transformations. Once a batch of data is prepared, it sends an event with key `data_prepared`.
2. A `training` task starts as long as the scheduler receives an event with key `data_prepared`, the task trains a new model with the latest dataset.
3. A `validating` task starts after the `training` task finishes with status `SUCCEED` and does the model validation. If the new model is better than the deployed one, it will send an event with key `model_validated`.
4. A `deploying` task starts as long as the scheduler receives an event with key `model_validated`, the task deploys the latest model to online serving and send an event with key `model_deployed`.
5. A `predicting` task keeps running and listening to the events with key `model_deployed`, it would predict with the new deployed model as long as receiving the event.

## Writing the Workflow
Now let us write the above workflow step by step.

As we mentioned in the [Workflow concept](../concepts/workflows.md), we need to write a Python script to act as a configuration file specifying the Workflow's structure.
Currently, the workflow needs to contain all user-defined classes and functions in the same Python file to avoid dependency conflicts because AIFlow need to compile the Workflow object in AIFlow server and workers.

### Importing Modules
As the workflow is defined in a Python script, we need to import the libraries we need.
```{note}
The libraries that we imports need to be installed on AIFlow server and workers in advance to avoid importing error.
```
```python
import logging
import os
import shutil
import time
import numpy as np

from typing import List
from joblib import dump, load

from sklearn.utils import check_random_state
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import LogisticRegression

from ai_flow import ops
from ai_flow.model.action import TaskAction
from ai_flow.operators.python import PythonOperator
from ai_flow.model.workflow import Workflow
from ai_flow.notification.notification_client import AIFlowNotificationClient, ListenerProcessor, Event
```

### Defining the Workflow

A Workflow is declared in a `with` statement, which includes all Tasks inside it.
When you initialize the Workflow, you need to give it a name(required) and a [namespace](../concepts/namespaces.md)(optional). 
If no namespace is assigned, the workflow belongs to `default` namespace. 

In the example, we create a workflow named `online_machine_learning`, belonging to `defalut` namespace. 
```python
with Workflow(name="online_machine_learning") as workflow:
    ...
```
Now let us define the AIFlow Tasks, note that the tasks defined in the workflow will run on different workers at different points in time, 
so no variables in memory should be passed between them to cross communicate.

### Defining the preprocessing Task

Here we create a `PythonOperator` that accepts a function as a parameter to preprocess dataset before training.
As we mentioned in the [Operator concept](../concepts/operators.md), an Operator that is instantiated can be called Task, 
so we could say that we create a Task named `preprocessing` in Workflow `online_machine_learning`.
```{note}
The definition of the Task should always be under the `with` statement of the Workflow that contains it.
```

We use a while loop to simulate continuous data generation and transformation. In each loop, we transform the dataset with sklearn API and save the new dataset to local file, 
then we send an Event with `AIFlowNotificationClient` to notify that a new batch of data has been prepared.

```python
with Workflow(name="online_machine_learning") as workflow:
    preprocess_task = PythonOperator(name="pre_processing",
                                     python_callable=preprocess)


def _prepare_working_dir():
    for path in [trained_model_dir, validated_model_dir, deployed_model_dir]:
        if not os.path.isdir(path):
            os.makedirs(path)


def _preprocess_data(dataset_uri):
    with np.load(dataset_uri) as f:
        x_data, y_data = f['x_train'], f['y_train']

    random_state = check_random_state(0)
    permutation = random_state.permutation(x_data.shape[0])
    x_train = x_data[permutation]
    y_train = y_data[permutation]

    reshaped_x_train = x_train.reshape((x_train.shape[0], -1))
    scaler_x_train = StandardScaler().fit_transform(reshaped_x_train)
    return scaler_x_train, y_train


def preprocess():
    _prepare_working_dir()
    train_dataset = dataset_path.format('train')
    try:
        event_sender = AIFlowNotificationClient(NOTIFICATION_SERVER_URI)
        while True:
            x_train, y_train = _preprocess_data(train_dataset)
            np.save(os.path.join(working_dir, f'x_train'), x_train)
            np.save(os.path.join(working_dir, f'y_train'), y_train)
            event_sender.send_event(key="data_prepared", value=None)
            time.sleep(30)
    finally:
        event_sender.close()
```

### Defining the training Task

The `training` task loads the dataset that is preprocessed and trains a model with Logistic Regression algorithm, and then save the model to the local directory `trained_models`.
The `training` task has a [Task Rule](../concepts/task_rules.md) declared by `action_on_event_received` API, 
which means that the `training` task takes the action `START` as long as an event with key `data_prepared` happened. 
```python
with Workflow(name="online_machine_learning") as workflow:
    train_task = PythonOperator(name="training",
                                python_callable=train)
    train_task.action_on_event_received(action=TaskAction.START, event_key="data_prepared")


def train():
    _prepare_working_dir()
    clf = LogisticRegression(C=50. / 5000, penalty='l1', solver='saga', tol=0.1)
    x_train = np.load(os.path.join(working_dir, f'x_train.npy'))
    y_train = np.load(os.path.join(working_dir, f'y_train.npy'))
    clf.fit(x_train, y_train)
    model_path = os.path.join(trained_model_dir, time.strftime("%Y%m%d%H%M%S", time.localtime()))
    dump(clf, model_path)
```

### Defining the validating Task

The `validating` task loads and proprocess the validation dataset and score the latest model with cross validation.
If the score of the new trained model is better than the current deployed one, send an event with key `model_validated` to notify that a better model is generated.

The `validating` task also has a [Task Rule](../concepts/task_rules.md) which is declared by `start_after` API, 
which means that the `validating` starts right after the `training` succeeds. 
```python
with Workflow(name="online_machine_learning") as workflow:
    validate_task = PythonOperator(name="validating",
                                   python_callable=validate)
    validate_task.start_after(train_task)


def validate():
    _prepare_working_dir()

    validate_dataset = dataset_path.format('evaluate')
    x_validate, y_validate = _preprocess_data(validate_dataset)

    to_be_validated = _get_latest_model(trained_model_dir)
    clf = load(to_be_validated)
    scores = cross_val_score(clf, x_validate, y_validate, scoring='precision_macro')
    try:
        event_sender = AIFlowNotificationClient(NOTIFICATION_SERVER_URI)
        deployed_model = _get_latest_model(deployed_model_dir)
        if deployed_model is None:
            logging.info(f"Generate the 1st model with score: {scores}")
            shutil.copy(to_be_validated, validated_model_dir)
            event_sender.send_event(key="model_validated", value=None)
        else:
            deployed_clf = load(deployed_model)
            old_scores = cross_val_score(deployed_clf, x_validate, y_validate, scoring='precision_macro')
            if np.mean(scores) > np.mean(old_scores):
                logging.info(f"A new model with score: {scores} passes validation")
                shutil.copy(to_be_validated, validated_model_dir)
                event_sender.send_event(key="model_validated", value=None)
            else:
                logging.info(f"New generated model with score: {scores} is worse "
                             f"than the previous: {old_scores}, ignored.")
    finally:
        event_sender.close()
```

### Defining the deploying Task

The `deploying` task simulates the deployment by copying the model from the directory `validated_models` to `deployed_models`.
After deploying the model, the task will send an event with key `model_deployed` to notify that the new model has been deployed.

The `deploying` task also has a [Task Rule](../concepts/task_rules.md) which is declared by `action_on_event_received` API, 
which means that the `deploying` starts as long as an event with key `model_validated` happened.

```python
with Workflow(name="online_machine_learning") as workflow:
    deploy_task = PythonOperator(name="deploying",
                                 python_callable=deploy)
    deploy_task.action_on_event_received(action=TaskAction.START, event_key="model_validated")


def deploy():
    _prepare_working_dir()
    to_be_deployed = _get_latest_model(validated_model_dir)
    deploy_model_path = shutil.copy(to_be_deployed, deployed_model_dir)
    try:
        event_sender = AIFlowNotificationClient(NOTIFICATION_SERVER_URI)
        event_sender.send_event(key="model_deployed", value=deploy_model_path)
    finally:
        event_sender.close()
```

### Defining the predicting Task

In the `predicting` task, we create a custom event listener to keep listening to events with key `model_deployed`, when it receives the event, it will predict with the latest deployed model. 
The `predicting` task has no [Task Rules](../concepts/task_rules.md) so it will start as long as the workflow begins.

```python
class ModelLoader(ListenerProcessor):
    def __init__(self):
        self.current_model = None
        logging.info("Waiting for the first model deployed...")

    def process(self, events: List[Event]):
        for e in events:
            self.current_model = e.value


def predict():
    _prepare_working_dir()
    predict_dataset = dataset_path.format('predict')
    result_path = os.path.join(working_dir, 'predict_result')
    x_predict, _ = _preprocess_data(predict_dataset)

    model_loader = ModelLoader()
    current_model = model_loader.current_model
    try:
        event_listener = AIFlowNotificationClient(NOTIFICATION_SERVER_URI)
        event_listener.register_listener(listener_processor=model_loader,
                                         event_keys=["model_deployed", ])
        while True:
            if current_model != model_loader.current_model:
                current_model = model_loader.current_model
                logging.info(f"Predicting with new model: {current_model}")
                clf = load(current_model)
                result = clf.predict(x_predict)
                with open(result_path, 'a') as f:
                    f.write(f'model [{current_model}] predict result: {result}\n')
            time.sleep(5)
    finally:
        event_listener.close()
```

## Running the Example

To get the full example along with the dataset, please download them from [github](https://github.com/flink-extended/ai-flow/tree/master/samples/online_machine_learning).

### Uploading the Workflow
Now we have a complete online machine learning workflow and its required dataset. Let's upload them to AIFlow server.
```shell script
aiflow workflow upload ${path_to_workflow_file} --files ${path_to_dataset_directory}
```
The workflow is uploaded successfully if you see `Workflow: default.online_machine_learning, submitted.` on the console.

### Starting the Workflow
In AIFlow, starting a workflow is creating a new [workflow execution](../concepts/workflow_executions.md), you can do this by the following command.

```shell script
aiflow workflow-execution start online_machine_learning
```
The workflow execution is started if you see `Workflow execution: {} submitted.` on the console.
You can view the workflow execution you just created by `list` command:
```shell script
aiflow workflow-execution list online_machine_learning
```

### Viewing the results
You can view the status of the tasks by the following command:
```shell script
aiflow task-execution list ${workflow_execution_id}
```
Also you can view the prediction output in the file `${AIFLOW_HOME}/working_dir/online_machine_learning/*/online_ml_workflow/tmp/predict_result`

If you want to view logs, you can go to check logs under the directory `${AIFLOW_HOME}/logs/online_machine_learning/`. The log files will give you the information in detail.

### Stopping the Workflow Execution

The `online_machine_learning` workflow contains streaming tasks that will never stop. If you want to stop the workflow execution, you can run the following command:
```shell script
aiflow workflow-execution stop-all online_machine_learning
``` 

## What's Next

Congratulations! You have been equipped with the necessary knowledge to write your own workflow. At this point, you can check [Examples](./examples.md) for more examples and [concepts](../concepts/index.md) to write your own workflows.
