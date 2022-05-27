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

from ai_flow.model.status import TaskStatus, TASK_FINISHED_SET, TASK_ALIVE_SET


class TestTaskStatus(unittest.TestCase):

    def test_status_in_set(self):
        self.assertTrue(TaskStatus.INIT in TASK_ALIVE_SET)
        self.assertTrue(TaskStatus.INIT.value in TASK_ALIVE_SET)
        self.assertTrue(TaskStatus.QUEUED in TASK_ALIVE_SET)
        self.assertTrue(TaskStatus.QUEUED.value in TASK_ALIVE_SET)
        self.assertTrue(TaskStatus.RETRYING in TASK_ALIVE_SET)
        self.assertTrue(TaskStatus.RETRYING.value in TASK_ALIVE_SET)
        self.assertTrue(TaskStatus.RESTARTING in TASK_ALIVE_SET)
        self.assertTrue(TaskStatus.RESTARTING.value in TASK_ALIVE_SET)
        self.assertTrue(TaskStatus.RUNNING in TASK_ALIVE_SET)
        self.assertTrue(TaskStatus.RUNNING.value in TASK_ALIVE_SET)

        self.assertFalse('INI' in TASK_ALIVE_SET)

        self.assertTrue(TaskStatus.SUCCESS in TASK_FINISHED_SET)
        self.assertTrue(TaskStatus.SUCCESS.value in TASK_FINISHED_SET)
        self.assertTrue(TaskStatus.FAILED in TASK_FINISHED_SET)
        self.assertTrue(TaskStatus.FAILED.value in TASK_FINISHED_SET)
        self.assertTrue(TaskStatus.KILLED in TASK_FINISHED_SET)
        self.assertTrue(TaskStatus.KILLED.value in TASK_FINISHED_SET)


if __name__ == '__main__':
    unittest.main()
