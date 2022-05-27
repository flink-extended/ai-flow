# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
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
import multiprocessing
import threading
from multiprocessing.managers import SyncManager
from typing import Optional

from kubernetes import client
from kubernetes.client import V1Pod
from kubernetes.client.rest import ApiException

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.model.task_execution import TaskExecutionKey
from ai_flow.task_executor.task_executor import BaseTaskExecutor
from .helpers import make_safe_label_value, POISON, get_kube_client
from .kube_config import KubeConfig
from .kube_scheduler import KubernetesScheduler
from .kube_watcher import KubernetesJobWatcher, ResourceVersion
from ai_flow.common.configuration import config_constants
from ai_flow.common.util.thread_utils import StoppableThread

logger = logging.getLogger(__name__)


class KubernetesTaskExecutor(BaseTaskExecutor):
    def __init__(self):
        self.manager: Optional[SyncManager] = None
        self.task_queue: Optional['Queue[TaskExecutionKey]'] = None
        self.kube_scheduler: Optional[KubernetesScheduler] = None
        self.kube_watcher: Optional[KubernetesJobWatcher] = None
        self.kube_config = KubeConfig(config_constants.K8S_TASK_EXECUTOR_CONFIG)
        self.kube_client = get_kube_client(in_cluster=self.kube_config.is_in_cluster(),
                                           config_file=self.kube_config.get_config_file())
        self._process_observer = StoppableThread(target=self._check_watcher_alive)

    def start_task_execution(self, key: TaskExecutionKey):
        if not self.task_queue:
            raise AIFlowException('KubernetesTaskExecutor not started.')
        self.task_queue.put(key)

    def stop_task_execution(self, key: TaskExecutionKey):
        dict_string = "workflow_execution_id={},task_name={},seq_number={}".format(
            make_safe_label_value(key.workflow_execution_id),
            make_safe_label_value(key.task_name),
            make_safe_label_value(key.seq_num),
        )
        kwargs = dict(label_selector=dict_string)
        pod_list = self.kube_client.list_namespaced_pod(namespace=self.kube_config.get_namespace(), **kwargs)
        for pod in pod_list.items:
            self.delete_pod(pod, self.kube_config.get_namespace())

    def start(self):
        logger.info('Starting Kubernetes Task Executor')
        self.manager = multiprocessing.Manager()
        self.task_queue = self.manager.Queue()
        self.kube_scheduler = KubernetesScheduler(self.kube_config,
                                                  self.task_queue,
                                                  self.kube_client)
        self.kube_scheduler.start()
        self.kube_watcher = self.create_kube_watcher()
        self._process_observer.start()

    def stop(self):
        if not self.manager:
            raise AIFlowException("The executor should be started first!")
        self._process_observer.stop()
        self._process_observer.join()

        self.task_queue.put(POISON)
        self.task_queue.join()

        self.kube_watcher.terminate()
        self.kube_watcher.join()
        self.kube_scheduler.terminate()
        self.kube_scheduler.join()

        self.manager.shutdown()

    def create_kube_watcher(self) -> KubernetesJobWatcher:
        resource_version = ResourceVersion().resource_version
        watcher = KubernetesJobWatcher(
            namespace=self.kube_config.get_namespace(),
            resource_version=resource_version,
            kube_config=self.kube_config,
        )
        watcher.start()
        return watcher

    def _check_watcher_alive(self):
        while not threading.current_thread().stopped():
            try:
                if not self.kube_watcher.is_alive():
                    logger.error('Kube watcher died, recreating...')
                    self.kube_watcher = self.create_kube_watcher()
            except Exception as e:
                logger.exception("Error occurred while checking kube watcher, {}".format(e))
        logger.info("Check process alive thread exiting.")

    def delete_pod(self, pod: V1Pod, namespace: str) -> None:
        try:
            logger.debug("Deleting pod %s in namespace %s", pod.metadata.name, namespace)
            self.kube_client.delete_namespaced_pod(
                name=pod.metadata.name,
                namespace=namespace,
                body=client.V1DeleteOptions(**self.kube_config.get_delete_request_args()),
                **self.kube_config.get_client_request_args())
        except ApiException:
            logger.exception('Error occurred while deleting k8s pod.')
            raise
