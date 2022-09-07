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
import os
import threading
import time
import unittest
from subprocess import TimeoutExpired

import cloudpickle
import psutil

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.operators.bash import BashOperator
from ai_flow.model.workflow import Workflow


class TestBashOperator(unittest.TestCase):

    def test_start_bash(self):
        test_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), ".test_start_bash.test")
        open(test_file, 'a').close()
        self.assertTrue(os.path.isfile(test_file))
        with Workflow(name='workflow') as workflow:
            bash_operator = BashOperator(name='test_start_bash', bash_command='rm {}'.format(test_file))
        bash_operator.start(context={})
        bash_operator.await_termination(context={})
        self.assertEqual(1, len(workflow.tasks))
        self.assertFalse(os.path.isfile(test_file))

    def test_non_zero_exit_code(self):
        with Workflow(name='workflow'):
            bash_operator = BashOperator(name='test_non_zero_exit_code', bash_command='exit 2')
        with self.assertRaisesRegex(
            AIFlowException, "Bash command failed\\. The command returned a non-zero exit code\\."
        ):
            bash_operator.start(context={})
            bash_operator.await_termination(context={})

    def test_stop(self):
        self.bash_operator = None

        def bash_op():
            with Workflow(name='workflow'):
                self.bash_operator = BashOperator(name='test_stop', bash_command='sleep 10')
            self.bash_operator.start(context={})
        _thread = threading.Thread(target=bash_op, daemon=True)
        _thread.start()

        time.sleep(0.1)
        self.bash_operator.stop(context={})
        time.sleep(0.1)
        with self.assertRaises(psutil.NoSuchProcess):
            psutil.Process(self.bash_operator.sub_process.pid)

    def test_await_termination(self):
        self.bash_operator = None

        with Workflow(name='workflow'):
            self.bash_operator = BashOperator(name='test_await_termination', bash_command='sleep 1')
        self.bash_operator.start(context={})

        with self.assertRaises(TimeoutExpired):
            time.sleep(0.1)
            self.bash_operator.await_termination(context={}, timeout=0.1)

    def test_pickle(self):
        with Workflow(name='workflow') as workflow:
            self.bash_operator = BashOperator(name='test_pickle', bash_command='sleep 1')
        self.assertIsNotNone(cloudpickle.dumps(workflow))
