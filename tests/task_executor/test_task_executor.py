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
import unittest
from unittest import mock

from ai_flow.task_executor.kubernetes.k8s_task_executor import KubernetesTaskExecutor
from ai_flow.task_executor.local.local_task_executor import LocalTaskExecutor
from ai_flow.task_executor.task_executor import TaskExecutorFactory


class TestTaskExecutor(unittest.TestCase):

    @mock.patch('ai_flow.task_executor.kubernetes.helpers.get_kube_client')
    def test_task_executor_factory(self, mock_client):
        self.assertEqual('ai_flow.task_executor.local.local_task_executor.LocalTaskExecutor',
                         TaskExecutorFactory.get_class_name('Local'))
        self.assertEqual('ai_flow.task_executor.kubernetes.k8s_task_executor.KubernetesTaskExecutor',
                         TaskExecutorFactory.get_class_name('KuBerneteS'))
        self.assertTrue(isinstance(TaskExecutorFactory.get_task_executor('local'), LocalTaskExecutor))
        self.assertTrue(isinstance(TaskExecutorFactory.get_task_executor('kubernetes'), KubernetesTaskExecutor))
        mock_client.assert_called_once()

