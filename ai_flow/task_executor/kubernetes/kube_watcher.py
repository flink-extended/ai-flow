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
import functools
import logging
from multiprocessing import Process
import time
from typing import Optional, Any, Dict

from ai_flow.model.task_execution import TaskExecutionKey
from urllib3.exceptions import ReadTimeoutError

from kubernetes import client, watch
from kubernetes.client import Configuration

from ai_flow.model.status import TaskStatus
from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.task_executor.kubernetes.helpers import get_kube_client
from ai_flow.task_executor.kubernetes.kube_config import KubeConfig

logger = logging.getLogger(__name__)


class KubernetesJobWatcher(Process):

    def __init__(
        self,
        namespace: Optional[str],
        resource_version: Optional[str],
        kube_config: Configuration,
    ):
        super().__init__()
        self.namespace = namespace
        self.resource_version = resource_version
        self.kube_config = kube_config
        super().__init__(target=self.watch)

    def watch(self) -> None:
        kube_client: client.CoreV1Api = get_kube_client()

        while True:
            try:
                self.resource_version = self._run(
                    kube_client, self.resource_version, self.kube_config
                )
            except ReadTimeoutError:
                logger.warning(
                    "Timeout to access the Kubernetes API. Retrying request.", exc_info=True
                )
                time.sleep(1)
            except Exception:
                logger.exception('Unknown error in KubernetesJobWatcher. Failing')
                raise
            else:
                logger.warning(
                    'Watch died gracefully, starting back up with: last resource_version: %s',
                    self.resource_version,
                )

    def _run(
        self,
        kube_client: client.CoreV1Api,
        resource_version: Optional[str],
        kube_config: KubeConfig,
    ) -> Optional[str]:
        logger.info('KubeWatcher start watching at resource_version: %s', resource_version)
        watcher = watch.Watch()

        kwargs = {}
        if resource_version:
            kwargs['resource_version'] = resource_version
        client_request_args = kube_config.get_client_request_args()
        if client_request_args:
            for key, value in client_request_args.items():
                kwargs[key] = value

        last_resource_version: Optional[str] = None
        list_worker_pods = functools.partial(
            watcher.stream, kube_client.list_namespaced_pod, self.namespace, **kwargs
        )
        for event in list_worker_pods():
            task = event['object']
            logger.debug('Event: %s had an event of type %s', task.metadata.name, event['type'])
            if event['type'] == 'ERROR':
                return self.process_error(event)

            annotations = task.metadata.annotations
            task_execution_related_annotations = {
                'workflow_execution_id': annotations['workflow_execution_id'],
                'task_name': annotations['task_name'],
                'seq_number': annotations['seq_number'],
            }
            self.process_status(
                pod_id=task.metadata.name,
                namespace=task.metadata.namespace,
                status=task.status.phase,
                annotations=task_execution_related_annotations,
                resource_version=task.metadata.resource_version,
                event=event,
            )
            last_resource_version = task.metadata.resource_version

        return last_resource_version

    def process_error(self, event: Any) -> str:
        logger.error('Error response from k8s list namespaced pod stream => %s', event)
        raw_object = event['raw_object']
        if raw_object['code'] == 410:
            logger.info(
                'Kubernetes resource version is too old, must reset to 0 => %s', (raw_object['message'],)
            )
            return '0'
        raise AIFlowException(
            'Kubernetes failure for %s with code %s and message: %s'
            % (raw_object['reason'], raw_object['code'], raw_object['message'])
        )

    def process_status(
        self,
        pod_id: str,
        namespace: str,
        status: str,
        annotations: Dict[str, str],
        resource_version: str,
        event: Any,
    ) -> None:
        event_str = self.event_details(pod_id, status, event['type'], resource_version)
        if status == 'Pending':
            if event['type'] == 'DELETED':
                logger.error('Set task status to FAILED after receiving event: %s', event_str)
                self._update_status(pod_id, TaskStatus.FAILED, annotations)
            else:
                logger.debug('Pod is pending %s', event_str)
        elif status == 'Failed':
            if event['type'] == 'DELETED':
                # Currently we use type=='DELETED' to judge the pod is killed instead of failure,
                # but before the pod is deleted, it will be 'MODIFIED' several times because of terminating operations.
                # So the status would be updated to FAILED firstly, and then eventually it will be set to KILLED
                # TODO replace the KILLED status judge logic, e.g. set to killing before deleting pod.
                logger.info('Set task status to KILLED after receiving event: %s', event_str)
                self._update_status(pod_id, TaskStatus.STOPPED, annotations)
            else:
                logger.error('Set task status to FAILED after receiving event: %s', event_str)
                self._update_status(pod_id, TaskStatus.FAILED, annotations)
        elif status == 'Succeeded':
            logger.info('Set task status to SUCCESS after receiving event: %s', event_str)
            self._update_status(pod_id, TaskStatus.SUCCESS, annotations)
        elif status == 'Running':
            logger.debug('Receiving event with status Running, event: %s', event_str)
        else:
            logger.warning(
                'Event: Invalid state: %s on pod: %s in namespace %s with annotations: %s with '
                'resource_version: %s',
                status,
                pod_id,
                namespace,
                annotations,
                resource_version,
            )

    @staticmethod
    def event_details(pod_id, status, event_type, resource_version):
        return 'pod: {}, pod status: {}, event_type: {}, resource_version: {}'.format(
            pod_id, status, event_type, resource_version
        )

    def _update_status(self, pod_id, status, annotations) -> None:
        logger.info(
            'Attempting to finish pod; pod_id: %s; state: %s; annotations: %s', pod_id, status, annotations
        )
        key = self._annotations_to_key(annotations=annotations)
        if key:
            logger.debug('finishing job %s - %s (%s)', key, status, pod_id)
            # TODO call scheduler interface to save meta
            logger.info("Save task execution {} with status {} to meta".format(key, status))

    @staticmethod
    def _annotations_to_key(annotations: Dict[str, str]) -> TaskExecutionKey:
        workflow_execution_id = annotations['workflow_execution_id']
        task_name = annotations['task_name']
        seq_num = int(annotations['seq_number'])
        return TaskExecutionKey(workflow_execution_id, task_name, seq_num)


class ResourceVersion:
    """Singleton for tracking resourceVersion from Kubernetes"""

    # TODO Persist the resource version to database, so that we can restore state of k8s event streams

    _instance = None
    resource_version = "0"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
