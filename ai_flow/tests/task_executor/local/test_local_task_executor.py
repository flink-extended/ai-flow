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

from ai_flow.common.configuration import config_constants
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
        pass

    def _test_execute_task(self):
        key = TaskExecutionKey(1, 'task', 1)
        command = ScheduleTaskCommand(key, TaskAction.START)

        executor = LocalTaskExecutor(parallelism=3)
        executor.start()
        executor.schedule_task(command)

        ret_key, status = executor.result_queue.get()
        self.assertEqual(str(key), str(ret_key))
        self.assertEqual(TaskStatus.SUCCESS, status)

        executor.stop()


if __name__ == '__main__':
    unittest.main()
