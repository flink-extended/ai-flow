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
import time
import unittest
from unittest import mock

from ai_flow.common.configuration import config_constants
from ai_flow.common.util.thread_utils import StoppableThread
from ai_flow.metadata import TaskExecutionMeta
from ai_flow.model.status import TaskStatus
from ai_flow.rpc.protobuf.heartbeat_service_pb2 import HeartbeatRequest

from ai_flow.task_executor.common.heartbeat_manager import HeartbeatManager
from ai_flow.task_executor.common import heartbeat_manager


class TestHeartbeatManager(unittest.TestCase):

    @mock.patch.object(config_constants, 'TASK_EXECUTOR_HEARTBEAT_CHECK_INTERVAL', 1)
    @mock.patch.object(config_constants, 'TASK_HEARTBEAT_TIMEOUT', 1)
    @mock.patch('ai_flow.task_executor.common.heartbeat_manager.HeartbeatManager._send_heartbeat_timeout')
    @mock.patch.object(heartbeat_manager, 'create_session')
    @mock.patch('ai_flow.task_executor.common.heartbeat_manager.get_notification_client')
    def test_rpc_server(self, mock_ns, mock_session, mock_send_timeout):
        manager = None
        try:
            expect_tasks = [
                TaskExecutionMeta(i, f'task_{i}')
                for i in [1, 2, 3]
            ]
            mock_session.return_value.__enter__.return_value.query.return_value.\
                filter.return_value.all.return_value = expect_tasks
            mock_session.return_value.__enter__.return_value.query.return_value.\
                filter.return_value.scalar.return_value = TaskStatus.SUCCESS
            manager = HeartbeatManager()
            manager.start()
            self.assertEqual(3, len(manager.task_dict))

            mock_session.return_value.__enter__.return_value.query.return_value.\
                filter.return_value.all.return_value = []
            cnt = 0
            while 0 != len(manager.task_dict) and cnt < 100:
                cnt += 1
                time.sleep(0.1)
            self.assertTrue(cnt < 100)

            expect_tasks = [
                TaskExecutionMeta(i, f'task_{i}')
                for i in [1, 4]
            ]
            for t in expect_tasks:
                t.sequence_number = t.workflow_execution_id
            mock_session.return_value.__enter__.return_value.query.return_value.\
                filter.return_value.all.return_value = expect_tasks
            cnt = 0
            while 2 != len(manager.task_dict) and cnt < 100:
                cnt += 1
                time.sleep(0.1)
            self.assertTrue(cnt < 100)

            mock_session.return_value.__enter__.return_value.query.return_value.\
                filter.return_value.all.return_value = []
            cnt = 0
            while 1 != len(manager.task_dict) and cnt < 100:
                manager.service.send_heartbeat(HeartbeatRequest(workflow_execution_id=1,
                                                                task_name='task_1',
                                                                sequence_number=1), None)
                time.sleep(0.1)
                cnt += 1
            self.assertTrue(cnt < 100)
            self.assertEqual({'1_task_1_1'}, manager.task_dict.keys())
        finally:
            manager.stop()

    def test__string_to_task_execution_key(self):
        key = HeartbeatManager._string_to_task_execution_key('1_task_name_2')
        self.assertEqual('1', key.workflow_execution_id)
        self.assertEqual('task_name', key.task_name)
        self.assertEqual('2', key.seq_num)

    @mock.patch('ai_flow.task_executor.common.heartbeat_manager.get_notification_client')
    @mock.patch.object(heartbeat_manager, 'create_session')
    def test__update_running_tasks(self, mock_session, mock_ns):
        expect_tasks = [
            TaskExecutionMeta(i, f'task_{i}')
            for i in [1, 2, 3]
        ]
        mock_session.return_value.__enter__.return_value.query.return_value.\
            filter.return_value.all.return_value = expect_tasks
        manager = HeartbeatManager()
        manager._update_running_tasks()
        self.assertEqual(3, len(manager.task_dict))
        for t in expect_tasks:
            self.assertTrue(f'{t.workflow_execution_id}_{t.task_name}_{t.sequence_number}' in manager.task_dict)

        expect_tasks = [
            TaskExecutionMeta(i, f'task_{i}')
            for i in [1, 2, 4]
        ]
        mock_session.return_value.__enter__.return_value.query.return_value.\
            filter.return_value.all.return_value = expect_tasks
        manager._update_running_tasks()
        self.assertEqual(4, len(manager.task_dict))
        for t in expect_tasks:
            self.assertTrue(f'{t.workflow_execution_id}_{t.task_name}_{t.sequence_number}' in manager.task_dict)

    @mock.patch.object(config_constants, 'TASK_EXECUTOR_HEARTBEAT_CHECK_INTERVAL', 2)
    @mock.patch('ai_flow.task_executor.common.heartbeat_manager.HeartbeatManager._send_heartbeat_timeout')
    @mock.patch.object(heartbeat_manager, 'create_session')
    @mock.patch('ai_flow.task_executor.common.heartbeat_manager.get_notification_client')
    def test_running_task_timeout(self, mock_ns, mock_session, mock_send_heartbeat):
        mock_session.return_value.__enter__.return_value.query.return_value.\
            filter.return_value.scalar.return_value = TaskStatus.RUNNING

        manager = HeartbeatManager()
        manager.task_dict = {'1_t1_2': time.time() - 100}

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
    @mock.patch('ai_flow.task_executor.common.heartbeat_manager.get_notification_client')
    def test_finished_task_timeout(self, mock_ns, mock_session, mock_send_heartbeat):
        mock_session.return_value.__enter__.return_value.query.return_value.\
            filter.return_value.scalar.return_value = TaskStatus.SUCCESS

        manager = HeartbeatManager()
        manager.task_dict = {
            '1_t1_2': time.time() - 100,
            '1_t2_2': time.time()
        }

        heartbeat_check_thread = StoppableThread(
            target=manager._check_heartbeat_timeout)
        heartbeat_check_thread.start()
        time.sleep(1)
        mock_send_heartbeat.assert_not_called()
        heartbeat_check_thread.stop()
        heartbeat_check_thread.join()
        self.assertEqual(1, len(manager.task_dict))
        self.assertEqual({'1_t2_2'}, manager.task_dict.keys())



