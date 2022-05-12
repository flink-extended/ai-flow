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
import os
import subprocess
import unittest
from queue import Empty
from tempfile import TemporaryDirectory
from unittest import mock

import psutil

from ai_flow.common.configuration import config_constants
from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.model.action import TaskAction
from ai_flow.model.status import TaskStatus
from ai_flow.model.task_execution import TaskExecutionKey
from ai_flow.task_executor.local.local_task_executor import LocalTaskExecutor
from ai_flow.task_executor.task_executor import ScheduleTaskCommand


class TestLocalExecutor(unittest.TestCase):

    def test_execution_with_subprocess(self):
        with mock.patch.object(
            config_constants, 'EXECUTE_TASKS_IN_NEW_INTERPRETER', new_callable=mock.PropertyMock
        ) as option:
            option.return_value = True
            self._test_execute_task()

    def test_execution_with_fork(self):
        self._test_execute_task()

    def test_stop_task_execution(self):
        with TemporaryDirectory(prefix='test_local_task_executor') as tmp_dir:
            executor = LocalTaskExecutor(parallelism=1,
                                         registry_path=os.path.join(tmp_dir, 'tmp_registry'))
            executor.start()

            process = subprocess.Popen(args=['sleep', '10'], close_fds=True)
            executor.registry.set('key', process.pid)
            self.assertEqual('running', psutil.Process(process.pid).status())

            executor.stop_task_execution('key')
            process.wait(timeout=1)

            with self.assertRaises(psutil.NoSuchProcess):
                psutil.Process(process.pid)
            executor.stop()

    def _test_execute_task(self):
        key = TaskExecutionKey(1, 'task', 1)
        command = ScheduleTaskCommand(key, TaskAction.START)

        with TemporaryDirectory(prefix='test_local_task_executor') as tmp_dir:
            executor = LocalTaskExecutor(parallelism=3,
                                         registry_path=os.path.join(tmp_dir, 'tmp_registry'))
            executor.start()
            executor._task_status_observer.stop()
            executor._task_status_observer.join()
            executor.schedule_task(command)

            ret_key, status = executor.result_queue.get(timeout=1)
            self.assertEqual(str(key), str(ret_key))
            self.assertEqual(TaskStatus.SUCCESS, status)

            executor.stop()

    def test_task_observer_thread(self):
        key = TaskExecutionKey(1, 'task', 1)
        command = ScheduleTaskCommand(key, TaskAction.START)

        executor = LocalTaskExecutor(parallelism=3)
        executor.start()
        executor.schedule_task(command)
        with self.assertRaises(Empty):
            executor.result_queue.get(timeout=1)
        executor.stop()

    def test_negative_parallelism(self):
        with self.assertRaises(AIFlowException) as context:
            executor = LocalTaskExecutor(0)
            executor.start()
            self.assertTrue('Parallelism of LocalTaskExecutor should be a positive integer' in context.exception)
        with self.assertRaises(AIFlowException) as context:
            executor = LocalTaskExecutor(-1)
            executor.start()
            self.assertTrue('Parallelism of LocalTaskExecutor should be a positive integer' in context.exception)


if __name__ == '__main__':
    unittest.main()
