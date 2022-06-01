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
import unittest
from unittest import mock

from ai_flow.model.status import TaskStatus
from kubernetes.client import models as k8s
from ai_flow.task_executor.kubernetes.kube_watcher import KubernetesJobWatcher


class TestKubeWatcher(unittest.TestCase):
    def setUp(self):
        self.workflow_execution_id = '101'
        self.task_name = 'task_name'
        self.seq_num = 3
        self.watcher = KubernetesJobWatcher(
            namespace="ai-flow",
            resource_version="0",
            kube_config=mock.MagicMock(),
        )
        self.kube_client = mock.MagicMock()
        self.core_annotations = {
            'workflow_execution_id': str(self.workflow_execution_id),
            'task_name': self.task_name,
            'seq_number': str(self.seq_num),
        }
        self.pod = k8s.V1Pod(
            metadata=k8s.V1ObjectMeta(
                name="foo",
                annotations={**self.core_annotations},
                namespace="ai-flow",
                resource_version="1",
            ),
            status=k8s.V1PodStatus(phase="Pending"),
        )
        self.events = []

    @mock.patch('ai_flow.task_executor.kubernetes.kube_watcher.KubernetesJobWatcher._update_status')
    def test_process_status_pending_deleted(self, mock_updata_status):
        self.events.append({"type": 'DELETED', "object": self.pod})
        self._run()
        self.assert_called_once_with_status(mock_updata_status, TaskStatus.FAILED)

    @mock.patch('ai_flow.task_executor.kubernetes.kube_watcher.KubernetesJobWatcher._update_status')
    def test_process_status_failed(self, mock_updata_status):
        self.pod.status.phase = "Failed"
        self.events.append({"type": 'MODIFIED', "object": self.pod})
        self._run()
        self.assert_called_once_with_status(mock_updata_status, TaskStatus.FAILED)

    @mock.patch('ai_flow.task_executor.kubernetes.kube_watcher.KubernetesJobWatcher._update_status')
    def test_process_status_succeeded(self, mock_updata_status):
        self.pod.status.phase = "Succeeded"
        self.events.append({"type": 'MODIFIED', "object": self.pod})
        self._run()
        self.assert_called_once_with_status(mock_updata_status, TaskStatus.SUCCESS)

    @mock.patch('ai_flow.task_executor.kubernetes.kube_watcher.KubernetesJobWatcher._update_status')
    def test_process_status_running(self, mock_updata_status):
        self.events.append({"type": 'MODIFIED', "object": self.pod})
        self._run()
        mock_updata_status.assert_not_called()

        self.pod.status.phase = "Running"
        self.events.append({"type": 'MODIFIED', "object": self.pod})
        self._run()
        mock_updata_status.assert_not_called()

        self.pod.status.phase = "Unknown"
        self.events.append({"type": 'MODIFIED', "object": self.pod})
        self._run()
        mock_updata_status.assert_not_called()

    def _run(self):
        with mock.patch('ai_flow.task_executor.kubernetes.kube_watcher.watch') as mock_watch:
            mock_watch.Watch.return_value.stream.return_value = self.events
            latest_resource_version = self.watcher._run(
                self.kube_client,
                self.watcher.resource_version,
                self.watcher.kube_config,
            )
            assert self.pod.metadata.resource_version == latest_resource_version

    def assert_called_once_with_status(self, mock_func, status):
        mock_func.assert_called_once_with(
                self.pod.metadata.name,
                status,
                self.core_annotations,)
