#
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
import time
import unittest

from ai_flow.common.util.thread_utils import StoppableThread


class TestStoppableThread(StoppableThread):
    def run(self) -> None:
        while not self.stopped():
            time.sleep(1)
            print('waiting...')


class TestThreadUtils(unittest.TestCase):

    def test_stoppable_thread(self):
        test_thread = TestStoppableThread()
        test_thread.start()
        time.sleep(1)
        test_thread.stop()
        test_thread.join()
        self.assertTrue(test_thread.stopped())
