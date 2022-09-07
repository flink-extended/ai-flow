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
import threading
import time
import unittest

import cloudpickle
import psutil

from ai_flow.operators.python import PythonOperator
from ai_flow.model.workflow import Workflow


def func(secs):
    time.sleep(secs)


class TestPythonOperator(unittest.TestCase):

    def test_python_operator(self):
        def func(arg1, arg2):
            self.assertEqual(1, arg1)
            self.assertEqual('any', arg2)

        with Workflow(name='workflow'):
            python_operator = PythonOperator(
                name='test_python_operator',
                python_callable=func,
                op_args=[1, 'any'],
            )
        python_operator.start(context=None)

    def test_pickle(self):
        with Workflow(name='workflow') as workflow:
            python_operator = PythonOperator(
                name='test_await_termination',
                python_callable=func,
                op_args=[1],
            )
        self.assertIsNotNone(cloudpickle.dumps(workflow))
