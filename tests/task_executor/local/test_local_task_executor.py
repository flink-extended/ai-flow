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
import subprocess
import threading
import time
import unittest
import psutil
from tempfile import TemporaryDirectory
from unittest import mock

from ai_flow.common.configuration import config_constants
from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.common.util.local_registry import LocalRegistry
from ai_flow.model.task_execution import TaskExecutionKey
from ai_flow.task_executor.local.local_task_executor import LocalTaskExecutor


class TestLocalExecutor(unittest.TestCase):

    @mock.patch('subprocess.Popen')
    @mock.patch('ai_flow.task_executor.common.task_executor_base.TaskExecutorBase.generate_command')
    def test_execution_with_subprocess(self, mock_command, mock_popen):
        mock_popen.return_value.pid = 1
        mock_popen.return_value.communicate.return_value = (b"OUT", b"ERR")
        mock_popen.return_value.poll.return_value = 0
        mock_command.return_value = None
        key = TaskExecutionKey(1, 'task', 1)

        with TemporaryDirectory(prefix='test_local_task_executor') as tmp_dir:
            executor = LocalTaskExecutor(parallelism=3,
                                         registry_path=os.path.join(tmp_dir, 'tmp_registry'))
            executor.initialize()
            # call start twice
            executor.start_task_execution(key)
            mock_command.assert_called_once_with(key)
            executor.start_task_execution(key)
            time.sleep(1)

            registry = LocalRegistry(os.path.join(tmp_dir, 'tmp_registry'))
            self.assertEqual(1, int(registry.get(str(key))))
            self.assertEqual(1, len(registry._db.keys()))
            executor.destroy()

    def test_stop_task_execution(self):

        def _stop(local_executor):
            time.sleep(1)
            local_executor.stop_task_execution('key')

        with TemporaryDirectory(prefix='test_local_task_executor') as tmp_dir:
            executor = LocalTaskExecutor(parallelism=1,
                                         registry_path=os.path.join(tmp_dir, 'tmp_registry'))
            process = subprocess.Popen(args=['sleep', '10'], close_fds=True)
            registry = LocalRegistry(os.path.join(tmp_dir, 'tmp_registry'))
            registry.set('key', process.pid)
            threading.Thread(target=_stop, args=(executor,)).start()
            process.wait()
            with self.assertRaises(psutil.NoSuchProcess):
                psutil.Process(process.pid)

    @mock.patch.object(config_constants, 'TASK_EXECUTOR_HEARTBEAT_CHECK_INTERVAL', 1)
    @mock.patch('ai_flow.task_executor.common.task_executor_base.HeartbeatManager')
    @mock.patch('ai_flow.task_executor.common.task_executor_base.get_notification_client')
    def test_negative_parallelism(self, mock_ns, mock_heartbeat):
        with self.assertRaises(AIFlowException) as context:
            try:
                executor = LocalTaskExecutor(0)
                executor.start()
                self.assertTrue('Parallelism of LocalTaskExecutor should be a positive integer' in context.exception)
            finally:
                executor.stop()
        with self.assertRaises(AIFlowException) as context:
            try:
                executor = LocalTaskExecutor(-1)
                executor.start()
                self.assertTrue('Parallelism of LocalTaskExecutor should be a positive integer' in context.exception)
            finally:
                executor.stop()


if __name__ == '__main__':
    unittest.main()
