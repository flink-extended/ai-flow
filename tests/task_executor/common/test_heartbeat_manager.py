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
import time
import unittest
from unittest import mock

from ai_flow.common.configuration import config_constants
from ai_flow.common.util.thread_utils import StoppableThread
from ai_flow.model.status import TaskStatus
from ai_flow.rpc.protobuf.heartbeat_service_pb2 import HeartbeatRequest

from ai_flow.task_executor.common.heartbeat_manager import HeartbeatManager
from ai_flow.task_executor.common import heartbeat_manager


class TestHeartbeatManager(unittest.TestCase):

    @mock.patch.object(config_constants, 'TASK_EXECUTOR_HEARTBEAT_CHECK_INTERVAL', 1)
    @mock.patch.object(config_constants, 'TASK_HEARTBEAT_TIMEOUT', 1)
    @mock.patch('ai_flow.task_executor.common.heartbeat_manager.HeartbeatManager._send_heartbeat_timeout')
    @mock.patch.object(heartbeat_manager, 'create_session')
    def test_rpc_server(self, mock_session, mock_send_timeout):
        manager = None
        try:
            mock_session.return_value.__enter__.return_value.query.return_value.\
                filter.return_value.all.return_value = [1, 2, 3]
            mock_session.return_value.__enter__.return_value.query.return_value.\
                filter.return_value.scalar.return_value = TaskStatus.SUCCESS
            manager = HeartbeatManager(None)
            manager.start()
            self.assertEqual(3, len(manager.task_dict))

            mock_session.return_value.__enter__.return_value.query.return_value.\
                filter.return_value.all.return_value = []
            cnt = 0
            while 0 != len(manager.task_dict) and cnt < 100:
                cnt += 1
                time.sleep(0.1)
            self.assertTrue(cnt < 100)

            mock_session.return_value.__enter__.return_value.query.return_value.\
                filter.return_value.all.return_value = [1, 4]
            cnt = 0
            while 2 != len(manager.task_dict) and cnt < 100:
                cnt += 1
                time.sleep(0.1)
            self.assertTrue(cnt < 100)

            mock_session.return_value.__enter__.return_value.query.return_value.\
                filter.return_value.all.return_value = []
            cnt = 0
            while 1 != len(manager.task_dict) and cnt < 100:
                manager.service.send_heartbeat(HeartbeatRequest(task_execution_id=1), None)
                time.sleep(0.1)
                cnt += 1
            self.assertTrue(cnt < 100)
            self.assertEqual({1}, manager.task_dict.keys())
        finally:
            manager.stop()

    @mock.patch.object(heartbeat_manager, 'create_session')
    def test__update_running_tasks(self, mock_session):
        expect_tasks = ['t1', 't2', 't3']
        mock_session.return_value.__enter__.return_value.query.return_value.\
            filter.return_value.all.return_value = expect_tasks
        manager = HeartbeatManager(None)
        manager._update_running_tasks()
        self.assertEqual(3, len(manager.task_dict))
        for t in expect_tasks:
            self.assertTrue(t in manager.task_dict)

        expect_tasks = ['t1', 't2', 't4']
        mock_session.return_value.__enter__.return_value.query.return_value.\
            filter.return_value.all.return_value = expect_tasks
        manager._update_running_tasks()
        self.assertEqual(4, len(manager.task_dict))
        for t in expect_tasks:
            self.assertTrue(t in manager.task_dict)

    @mock.patch.object(config_constants, 'TASK_EXECUTOR_HEARTBEAT_CHECK_INTERVAL', 2)
    @mock.patch('ai_flow.task_executor.common.heartbeat_manager.HeartbeatManager._send_heartbeat_timeout')
    @mock.patch.object(heartbeat_manager, 'create_session')
    def test_running_task_timeout(self, mock_session, mock_send_heartbeat):
        mock_session.return_value.__enter__.return_value.query.return_value.\
            filter.return_value.scalar.return_value = TaskStatus.RUNNING

        manager = HeartbeatManager(None)
        manager.task_dict = {'t1': time.time() - 100}

        heartbeat_check_thread = StoppableThread(
            target=manager._check_heartbeat_timeout)
        heartbeat_check_thread.start()
        time.sleep(1)
        mock_send_heartbeat.assert_called_once()
        heartbeat_check_thread.stop()
        heartbeat_check_thread.join()

    @mock.patch.object(config_constants, 'TASK_EXECUTOR_HEARTBEAT_CHECK_INTERVAL', 1)
    @mock.patch('ai_flow.task_executor.common.heartbeat_manager.HeartbeatManager._send_heartbeat_timeout')
    @mock.patch.object(heartbeat_manager, 'create_session')
    def test_finished_task_timeout(self, mock_session, mock_send_heartbeat):
        mock_session.return_value.__enter__.return_value.query.return_value.\
            filter.return_value.scalar.return_value = TaskStatus.SUCCESS

        manager = HeartbeatManager(None)
        manager.task_dict = {
            't1': time.time() - 100,
            't2': time.time()
        }

        heartbeat_check_thread = StoppableThread(
            target=manager._check_heartbeat_timeout)
        heartbeat_check_thread.start()
        time.sleep(1)
        mock_send_heartbeat.assert_not_called()
        heartbeat_check_thread.stop()
        heartbeat_check_thread.join()
        self.assertEqual(1, len(manager.task_dict))
        self.assertEqual({'t2'}, manager.task_dict.keys())



