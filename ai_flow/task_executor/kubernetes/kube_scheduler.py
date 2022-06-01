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
import json
import logging
from multiprocessing import Process
from queue import Queue

from ai_flow.common.exception.exceptions import AIFlowConfigException
from kubernetes.client import V1PodList, V1Pod

from ai_flow.model.task_execution import TaskExecutionKey
from kubernetes import client
from kubernetes.client.rest import ApiException

from ai_flow.model.status import TaskStatus
from ai_flow.task_executor.kubernetes.helpers import create_pod_id, key_to_label_selector, POISON, \
    gen_command
from ai_flow.task_executor.kubernetes.kube_config import KubeConfig
from ai_flow.task_executor.kubernetes.pod_generator import PodGenerator

logger = logging.getLogger(__name__)


class KubernetesScheduler(Process):

    def __init__(
        self,
        kube_config: KubeConfig,
        task_queue: 'Queue[TaskExecutionKey]',
        kube_client: client.CoreV1Api,
    ):
        self.kube_config = kube_config
        self.task_queue = task_queue
        self.kube_client = kube_client
        self.namespace = self.kube_config.get_namespace()
        super().__init__(target=self.schedule)

    def schedule(self):
        while True:
            try:
                key = self.task_queue.get()
                if key is POISON:
                    logger.info("Receiving the poison, breaking the loop...")
                    break

                label_selector = key_to_label_selector(key)
                if len(self.list_pods(label_selector)) > 0:
                    logger.warning(f'TaskExecution: {key} has been submitted in the past, skipping...')
                    continue

                logger.debug(f'Submitting TaskExecution: {key}.')
                self._run(key)
            except ApiException as e:
                if e.reason == "BadRequest":
                    logger.error("Request was invalid. Failing task")
                    # TODO call scheduler interface to save meta
                    print("Save task execution {} with status {} to meta".format(key, TaskStatus.FAILED))
                else:
                    logger.warning(
                        'ApiException when attempting to run task, re-queueing. Message: %s',
                        json.loads(e.body)['message'],
                    )
                    self.task_queue.put(key)
            except Exception as ex:
                logger.exception('Error occurred during schedule task, {}'.format(str(ex)))
            finally:
                self.task_queue.task_done()
        logger.info("Exiting kubernetes task scheduler...")

    def _run(self, key: TaskExecutionKey) -> None:
        command = gen_command(key)
        logger.info('Running job %s %s', str(key), str(command))

        template_file = self.kube_config.get_pod_template_file()
        if template_file is None:
            raise AIFlowConfigException('Option pod_template_file of kubernetes is not set.')
        base_worker_pod = PodGenerator.get_base_pod_from_template(template_file)
        pod = PodGenerator.construct_pod(
            workflow_execution_id=key.workflow_execution_id,
            task_name=key.task_name,
            seq_num=key.seq_num,
            try_number=1,
            pod_id=create_pod_id(key),
            kube_image=self.kube_config.get_image(),
            args=command,
            base_worker_pod=base_worker_pod,
            namespace=self.namespace
        )
        client_request_args = self.kube_config.get_client_request_args()
        client_request_args = {} if client_request_args is None else client_request_args
        self.run_pod_async(pod, **client_request_args)

    def list_pods(self, labels_selector: str):
        kwargs = dict(label_selector=labels_selector)
        pod_list: V1PodList = self.kube_client.list_namespaced_pod(namespace=self.kube_config.get_namespace(), **kwargs)
        return pod_list.items

    def run_pod_async(self, pod: V1Pod, **kwargs):

        sanitized_pod = self.kube_client.api_client.sanitize_for_serialization(pod)
        json_pod = json.dumps(sanitized_pod, indent=2)

        logger.debug('Pod Creation Request: \n%s', json_pod)
        try:
            resp = self.kube_client.create_namespaced_pod(
                body=sanitized_pod, namespace=pod.metadata.namespace, **kwargs
            )
            logger.debug('Pod Creation Response: %s', resp)
        except Exception as e:
            logger.exception('Exception when attempting to create Namespaced Pod: %s', json_pod)
            raise e
        return resp
