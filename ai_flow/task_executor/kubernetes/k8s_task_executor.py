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

from kubernetes import client
from kubernetes.client import V1Pod, V1PodList
from kubernetes.client.rest import ApiException

from . import helpers
from .helpers import key_to_label_selector, annotations_to_key
from .kube_config import KubeConfig
from .pod_generator import PodGenerator
from ..common.task_executor_base import TaskExecutorBase

from ai_flow.model.status import TaskStatus
from ai_flow.common.exception.exceptions import AIFlowConfigException
from ai_flow.model.task_execution import TaskExecutionKey
from ai_flow.common.configuration import config_constants

logger = logging.getLogger(__name__)


class KubernetesTaskExecutor(TaskExecutorBase):

    def __init__(self):
        self.kube_config = KubeConfig(config_constants.K8S_TASK_EXECUTOR_CONFIG)
        self.namespace = self.kube_config.get_namespace()
        self.kube_client = helpers.get_kube_client(in_cluster=self.kube_config.is_in_cluster(),
                                                   config_file=self.kube_config.get_config_file())
        super().__init__()

    def start_task_execution(self, key: TaskExecutionKey):
        if self._is_task_submitted(key):
            logger.warning(f'TaskExecution: {key} has been submitted in the past, skipping...')
            return

        command = self.generate_command(key)
        logger.info('Running job %s %s', str(key), str(command))
        template_file = self.kube_config.get_pod_template_file()
        if template_file is None or not os.path.exists(template_file):
            raise AIFlowConfigException(f'pod_template_file {template_file} of kubernetes not found.')
        try:
            base_worker_pod = PodGenerator.get_base_pod_from_template(template_file)
            pod = PodGenerator.construct_pod(
                workflow_execution_id=key.workflow_execution_id,
                task_name=key.task_name,
                seq_num=key.seq_num,
                kube_image=self.kube_config.get_image(),
                args=command,
                base_worker_pod=base_worker_pod,
                namespace=self.namespace
            )
            client_request_args = self.kube_config.get_client_request_args()
            client_request_args = {} if client_request_args is None else client_request_args
            helpers.run_pod(self.kube_client, pod, **client_request_args)
        except ApiException as e:
            logger.exception("ApiException when attempting to run task. Failing task, %s", e)
            self.status_queue.put((key, TaskStatus.FAILED))

    def stop_task_execution(self, key: TaskExecutionKey):
        label_selector = key_to_label_selector(key)
        pod_list = self._list_pods(label_selector)
        for pod in pod_list:
            self._delete_pod(pod, self.kube_config.get_namespace())

    def _delete_pod(self, pod: V1Pod, namespace: str) -> None:
        try:
            logger.debug("Deleting pod %s in namespace %s", pod.metadata.name, namespace)
            self.kube_client.delete_namespaced_pod(
                name=pod.metadata.name,
                namespace=namespace,
                body=client.V1DeleteOptions(**self.kube_config.get_delete_options()),
                **self.kube_config.get_client_request_args())
        except ApiException as e:
            logger.exception('Error occurred while deleting k8s pod, %s', e)
            raise e

    def _list_pods(self, labels_selector: str):
        kwargs = dict(label_selector=labels_selector)
        pod_list: V1PodList = self.kube_client.list_namespaced_pod(namespace=self.namespace, **kwargs)
        return pod_list.items

    def _is_task_submitted(self, key: TaskExecutionKey):
        label_selector = key_to_label_selector(key)
        pod_list = self._list_pods(label_selector)
        for pod in pod_list:
            key_from_annotations = annotations_to_key(pod.metadata.annotations)
            if str(key) == str(key_from_annotations):
                return True
        return False
