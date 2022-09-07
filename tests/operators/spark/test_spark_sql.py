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

from ai_flow.model.workflow import Workflow
from ai_flow.operators.spark.spark_sql import SparkSqlOperator


class TestSparkSqlOperator(unittest.TestCase):
    def setUp(self) -> None:
        with Workflow('w1'):
            operator = SparkSqlOperator(name='test_spark_submit',
                                        sql='SELECT * from dataframe',
                                        master='yarn',
                                        executable_path='/usr/bin/spark-submit',
                                        application_name='test_application')
        self.op: SparkSqlOperator = operator
        self.expect_command = ['spark-submit',
                               '--master', 'yarn',
                               '--deploy-mode', 'cluster',
                               '--name', 'test_application',
                               '--conf', 'spark.yarn.appMasterEnv.bar=foo',
                               '--conf', 'a=b',
                               './spark-examples.jar',
                               '1000']

    @mock.patch('ai_flow.operators.spark.spark_sql.SparkSqlOperator._get_executable_path')
    def test__build_spark_sql_command(self, mock_executable):
        mock_executable.return_value = 'spark-sql'
        a = self.op._build_spark_sql_command()
        print(a)

    @mock.patch('os.path.exists')
    def test__get_executable_path(self, mock_exists):
        with unittest.mock.patch.dict('os.environ', SPARK_HOME=os.path.dirname(__file__)):
            self.op._executable_path = None
            mock_exists.return_value = True
            self.assertEqual(os.path.join(os.path.dirname(__file__), 'bin/spark-sql'),
                             self.op._get_executable_path())
