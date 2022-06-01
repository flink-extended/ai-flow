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
import unittest
from unittest import mock
from ai_flow.task_executor.kubernetes.kube_scheduler import KubernetesScheduler


class TestKubernetesScheduler(unittest.TestCase):

    @mock.patch('ai_flow.task_executor.kubernetes.helpers.key_to_label_selector')
    def test_receive_poison(self, mock_func):
        mock_config = mock.MagicMock()
        mock_config.get_namespace.return_value = 'namespace'
        task_queue = queue.Queue()
        scheduler = KubernetesScheduler(kube_config=mock_config,
                                        task_queue=task_queue,
                                        kube_client=mock.MagicMock())
        task_queue.put(None)
        task_queue.put(mock.MagicMock())
        scheduler.schedule()
        mock_func.assert_not_called()

    @mock.patch('ai_flow.task_executor.kubernetes.kube_scheduler.KubernetesScheduler._run')
    @mock.patch('ai_flow.task_executor.kubernetes.kube_scheduler.KubernetesScheduler.list_pods')
    def test_submit_task_multi_times(self, mock_list_pids, mock_submit):
        mock_list_pids.return_value = ['']
        mock_config = mock.MagicMock()
        mock_config.get_namespace.return_value = 'namespace'
        task_queue = queue.Queue()
        scheduler = KubernetesScheduler(kube_config=mock_config,
                                        task_queue=task_queue,
                                        kube_client=mock.MagicMock())
        task_queue.put(mock.MagicMock())
        task_queue.put(None)
        scheduler.schedule()
        mock_submit.assert_not_called()


