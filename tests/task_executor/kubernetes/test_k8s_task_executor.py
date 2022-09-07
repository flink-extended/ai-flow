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
import os
import unittest
from unittest import mock
from ai_flow.model.task_execution import TaskExecutionKey
from ai_flow.task_executor.kubernetes.k8s_task_executor import KubernetesTaskExecutor


class TestK8sTaskExecutor(unittest.TestCase):

    @mock.patch('ai_flow.task_executor.kubernetes.k8s_task_executor.KubernetesTaskExecutor._list_pods')
    @mock.patch('ai_flow.task_executor.kubernetes.k8s_task_executor.KubernetesTaskExecutor._is_task_submitted')
    @mock.patch('ai_flow.task_executor.kubernetes.helpers.run_pod')
    @mock.patch('ai_flow.task_executor.kubernetes.helpers.get_kube_client')
    def test_run_existed_task(self, mock_client, mock_run_pod, mock_is_submmitted, mock_list_pods):
        executor = KubernetesTaskExecutor()
        key = TaskExecutionKey(1, 'task', 2)
        mock_is_submmitted.return_value = True
        executor.start_task_execution(key)
        mock_run_pod.assert_not_called()

    @mock.patch('ai_flow.task_executor.kubernetes.k8s_task_executor.KubernetesTaskExecutor._list_pods')
    @mock.patch('ai_flow.task_executor.kubernetes.helpers.get_kube_client')
    def test__is_task_submitted(self, mock_client, mock_list_pods):
        executor = KubernetesTaskExecutor()
        key = TaskExecutionKey(1, 'task', 3)
        expected = []
        for i in range(2):
            mock_pod = mock.MagicMock()
            mock_pod.metadata.annotations = {
                'workflow_execution_id': 1,
                'task_name': 'task',
                'seq_number': i
            }
            expected.append(mock_pod)
        mock_list_pods.return_value = expected
        self.assertFalse(executor._is_task_submitted(key))
        mock_pod = mock.MagicMock()
        mock_pod.metadata.annotations = {
            'workflow_execution_id': 1,
            'task_name': 'task',
            'seq_number': 3
        }
        expected.append(mock_pod)
        mock_list_pods.return_value = expected
        self.assertTrue(executor._is_task_submitted(key))

    @mock.patch('ai_flow.task_executor.kubernetes.k8s_task_executor.KubernetesTaskExecutor._list_pods')
    @mock.patch('ai_flow.task_executor.kubernetes.helpers.run_pod')
    @mock.patch('ai_flow.task_executor.kubernetes.helpers.get_kube_client')
    @mock.patch('ai_flow.task_executor.common.task_executor_base.TaskExecutorBase.generate_command')
    def test_start_task_execution_without_template(self, mock_command, mock_client, mock_run_pod, mock_list_pods):
        executor = KubernetesTaskExecutor()
        executor.kube_config.config['pod_template_file'] = None
        key = TaskExecutionKey(1, 'task', 2)
        mock_list_pods.return_value = []
        executor.start_task_execution(key)
        mock_command.assert_called_once_with(key)
        mock_run_pod.assert_called_once()

    @mock.patch('ai_flow.task_executor.kubernetes.k8s_task_executor.KubernetesTaskExecutor._list_pods')
    @mock.patch('ai_flow.task_executor.kubernetes.helpers.run_pod')
    @mock.patch('ai_flow.task_executor.kubernetes.helpers.get_kube_client')
    @mock.patch('ai_flow.task_executor.common.task_executor_base.TaskExecutorBase.generate_command')
    def test_start_task_execution(self, mock_command, mock_client, mock_run_pod, mock_list_pods):
        executor = KubernetesTaskExecutor()
        template_file = os.path.join(os.path.dirname(__file__), 'base_pod.yaml')
        executor.kube_config.config['pod_template_file'] = template_file
        key = TaskExecutionKey(1, 'task', 2)

        mock_list_pods.return_value = []

        executor.start_task_execution(key)
        mock_command.assert_called_once_with(key)
        mock_run_pod.assert_called_once()

    @mock.patch('ai_flow.task_executor.kubernetes.helpers.get_kube_client')
    @mock.patch('ai_flow.task_executor.kubernetes.k8s_task_executor.KubernetesTaskExecutor._delete_pod')
    @mock.patch('ai_flow.task_executor.kubernetes.k8s_task_executor.KubernetesTaskExecutor._list_pods')
    def test_stop_task_execution(self, mock_list_pods, mock_delete_func, mock_client):
        executor = KubernetesTaskExecutor()
        key = TaskExecutionKey(1, 'task', 2)
        mock_list_pods.return_value = [mock.MagicMock()]
        executor.stop_task_execution(key)
        mock_delete_func.assert_called_once()


