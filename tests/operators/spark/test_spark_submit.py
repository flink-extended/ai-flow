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
import os
import unittest
from unittest import mock

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.model.workflow import Workflow
from ai_flow.operators.spark.spark_submit import SparkSubmitOperator


class TestSparkSubmitOperator(unittest.TestCase):

    def setUp(self) -> None:
        with Workflow('w1'):
            operator = SparkSubmitOperator(name='test_spark_submit',
                                           application='./spark-examples.jar',
                                           application_args=['1000'],
                                           executable_path='/usr/bin/spark-submit',
                                           master='yarn',
                                           deploy_mode='cluster',
                                           application_name='test_application',
                                           submit_options='--conf a=b',
                                           k8s_namespace=None,
                                           env_vars={"bar": "foo"})
        self.op: SparkSubmitOperator = operator
        self.expect_command = ['spark-submit',
                               '--master', 'yarn',
                               '--deploy-mode', 'cluster',
                               '--name', 'test_application',
                               '--conf', 'spark.yarn.appMasterEnv.bar=foo',
                               '--conf', 'a=b',
                               './spark-examples.jar',
                               '1000']

    @mock.patch('ai_flow.operators.spark.spark_submit.SparkSubmitOperator._get_executable_path')
    def test__build_spark_submit_command(self, mock_executable):
        mock_executable.return_value = 'spark-submit'
        command = self.op._build_spark_submit_command()
        self.assertEqual(self.expect_command, command)

    @mock.patch('os.path.exists')
    def test__get_executable_path(self, mock_exists):
        with unittest.mock.patch.dict('os.environ', SPARK_HOME=os.path.dirname(__file__)):
            self.op._executable_path = None
            mock_exists.return_value = True
            self.assertEqual(os.path.join(os.path.dirname(__file__), 'bin/spark-submit'),
                             self.op._get_executable_path())

    def test__validate_parameters(self):
        self.op._deploy_mode = 'cluster'
        self.op._master = 'spark://foo:bar'
        with self.assertRaisesRegex(AIFlowException, 'Only client mode is supported with standalone cluster'):
            self.op._validate_parameters()
        self.op._master = 'mesos://foo:bar'
        with self.assertRaisesRegex(AIFlowException, 'Only client mode is supported with mesos cluster'):
            self.op._validate_parameters()
        self.op._master = 'k8s://foo:bar'
        self.op._is_kubernetes = True
        with self.assertRaisesRegex(AIFlowException, 'Param k8s_namespace must be set when submit to k8s'):
            self.op._validate_parameters()

    def test_process_spark_submit_log_yarn(self):
        log_lines = [
            '...',
            'INFO Client: Submitting application application_1658663952061_0020 ' + 'to ResourceManager',
            '...'
        ]
        self.op._process_spark_submit_log(log_lines)
        self.assertEqual('application_1658663952061_0020', self.op._yarn_application_id)

    def test_process_spark_submit_log_k8s(self):
        self.op._is_yarn = False
        self.op._is_kubernetes = True
        log_lines = ['pod name: spark-foobar-driver'
                     + 'namespace: default'
                     + 'Exit code: 1'
        ]
        self.op._process_spark_submit_log(log_lines)
        self.assertEqual('spark-foobar-driver', self.op._kubernetes_driver_pod)
        self.assertEqual(1, self.op._spark_exit_code)
