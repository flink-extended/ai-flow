#
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
import threading
import time
import unittest

import cloudpickle
import psutil

from ai_flow.model.operators.python import PythonOperator
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
                callable_args=[1, 'any'],
            )
        python_operator.start(context=None)

    def test_await_termination(self):
        with Workflow(name='workflow'):
            python_operator = PythonOperator(
                name='test_await_termination',
                python_callable=func,
                callable_args=[1],
            )
            python_operator.start(context=None)
        python_operator.await_termination(context=None, timeout=0.1)
        ps = psutil.Process(python_operator.process.pid)
        self.assertEqual('running', ps.status())

    def test_stop(self):
        self.python_operator = None

        def python_op():
            with Workflow(name='workflow'):
                self.python_operator = PythonOperator(name='test_await_termination',
                                                      python_callable=func,
                                                      callable_args=[100],)
            self.python_operator.start(context={})
        _thread = threading.Thread(target=python_op, daemon=True)
        _thread.start()
        time.sleep(0.1)
        self.python_operator.stop(context={})

        time.sleep(0.1)
        with self.assertRaises(psutil.NoSuchProcess):
            psutil.Process(self.python_operator.process.pid)

    def test_pickle(self):
        with Workflow(name='workflow') as workflow:
            python_operator = PythonOperator(
                name='test_await_termination',
                python_callable=func,
                callable_args=[1],
            )
        self.assertIsNotNone(cloudpickle.dumps(workflow))
