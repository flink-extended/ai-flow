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
import queue
import time
import unittest
from unittest import mock

from kubernetes.client import CoreV1Api

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.model.task_execution import TaskExecutionKey
from ai_flow.task_executor.kubernetes.helpers import make_safe_label_value
from ai_flow.task_executor.kubernetes.k8s_task_executor import KubernetesTaskExecutor
from ai_flow.task_executor.kubernetes.kube_config import KubeConfig


class TestK8sTaskExecutor(unittest.TestCase):

    @mock.patch('ai_flow.task_executor.kubernetes.helpers.get_kube_client')
    def test_start_task_execution(self, mock_kube_client):
        executor = KubernetesTaskExecutor()
        with self.assertRaises(AIFlowException):
            executor.start_task_execution(None)
        mock_kube_client.assert_called_once_with(config_file=None, in_cluster=False)

        executor.task_queue = queue.Queue()
        key = TaskExecutionKey(1, 'task', 1)
        executor.start_task_execution(key)
        self.assertEqual(key, executor.task_queue.get())

    @mock.patch('kubernetes.client.CoreV1Api.list_namespaced_pod')
    @mock.patch('kubernetes.client.CoreV1Api.delete_namespaced_pod')
    @mock.patch('ai_flow.task_executor.kubernetes.helpers.get_kube_client')
    def test_stop_task_execution(self, mock_client, mock_delete_func, mock_list_func):
        executor = KubernetesTaskExecutor()
        mock_client.assert_called_once_with(config_file=None, in_cluster=False)

        executor.kube_client = CoreV1Api()
        executor.kube_config = KubeConfig({'namespace': 'test'})

        dict_string = "workflow_execution_id={},task_name={},seq_number={}".format(
            make_safe_label_value(1),
            make_safe_label_value('task'),
            make_safe_label_value(1),
        )
        key = TaskExecutionKey(1, 'task', 1)

        mock_list_func.return_value.items = [mock.MagicMock()]
        executor.stop_task_execution(key)

        mock_list_func.assert_called_once_with(namespace='test', label_selector=dict_string)
        mock_delete_func.assert_called_once()
