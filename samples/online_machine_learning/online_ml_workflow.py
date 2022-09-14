# Copyright 2022 The AI Flow Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
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


if __name__ == "__main__":
    artifacts = os.path.join(os.path.dirname(__file__), "dataset")
    ops.upload_workflows(workflow_file_path=__file__,
                         artifacts=[artifacts, ])
    ops.start_workflow_execution("online_machine_learning")
