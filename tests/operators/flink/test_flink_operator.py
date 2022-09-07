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
import subprocess
import unittest
from unittest import mock

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.model.context import Context
from ai_flow.model.workflow import Workflow
from ai_flow.operators.flink.flink_operator import FlinkOperator


class TestFlinkOperator(unittest.TestCase):

    def setUp(self) -> None:
        with Workflow('w1'):
            operator = FlinkOperator(name='test_flink_operator',
                                     target='local',
                                     application='./flink-examples.jar',
                                     application_args=['1000'],
                                     executable_path='/usr/bin/flink',
                                     command_options='-Dfoo=bar')
        self.op: FlinkOperator = operator
        self.expect_command = ['spark-submit',
                               '--master', 'yarn',
                               '--deploy-mode', 'cluster',
                               '--name', 'test_application',
                               '--conf', 'spark.yarn.appMasterEnv.bar=foo',
                               '--conf', 'a=b',
                               './spark-examples.jar',
                               '1000']

    def test_await_termination(self):
        self.op._flink_run_cmd = ["flink", "run"]
        self.op._process = mock.MagicMock()
        self.op._process.stdout = [
            "Job has been submitted with JobID abc",
        ]
        self.op._process.wait.return_value = 1
        with self.assertRaisesRegex(AIFlowException, "Cannot execute: flink run. Error code is: 1"):
            self.op.await_termination(Context())

        self.op._process.wait.return_value = 0
        with mock.patch(
                "ai_flow.operators.flink.flink_operator.FlinkOperator._start_tracking_yarn_application_status"
        ) as mock_yarn_status:
            self.op._is_yarn_application_mode = True
            self.op._yarn_application_final_status = 'SUCCEEDED'
            self.op.await_termination(Context())
            mock_yarn_status.assert_called_once()

        with mock.patch(
                "ai_flow.operators.flink.flink_operator.FlinkOperator._start_tracking_k8s_application_status"
        ) as mock_k8s_status:
            with mock.patch(
                "ai_flow.operators.flink.flink_operator.FlinkOperator._retrieve_job_id_in_application_mode"
            ) as mock_job_id:
                self.op._is_yarn_application_mode = False
                self.op._is_kubernetes_application_mode = True
                self.op._k8s_application_job_status = 'FINISHED'
                self.op.await_termination(Context())
                mock_k8s_status.assert_called_once()
                mock_job_id.assert_called_once()

    @mock.patch('subprocess.Popen')
    @mock.patch("ai_flow.operators.flink.flink_operator.FlinkOperator._get_executable_path")
    def test_stop(self, mock_executable, mock_popen):
        self.op._process = mock.MagicMock()
        mock_executable.return_value = 'flink'
        with self.assertRaisesRegex(AIFlowException, 'Flink job id has not been obtained'):
            self.op.stop(Context())

        mock_popen.return_value.communicate.return_value = "stdout", "stderr"
        mock_popen.return_value.wait.return_value = 0
        self.op._target = 'remote'
        self.op._flink_job_id = 'abc'
        self.op._yarn_application_id = 'app_id'
        self.op._kubernetes_cluster_id = 'deployment_id'

        self.op._is_kubernetes_application_mode = True
        with mock.patch(
                "ai_flow.operators.flink.flink_operator.FlinkOperator._delete_cluster_in_k8s_application"
        ) as mock_delete:
            self.op.stop(Context())
            cmd = ['flink', 'cancel', '-t', "kubernetes-application", "-Dkubernetes.cluster-id=deployment_id", 'abc']
            mock_popen.assert_called_with(cmd,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE,
                                          universal_newlines=True)
            mock_delete.assert_called_once()

        self.op._is_kubernetes_session = True
        self.op._is_kubernetes_application_mode = False
        self.op.stop(Context())
        cmd = ['flink', 'cancel', '-t', "kubernetes-session", "-Dkubernetes.cluster-id=deployment_id", 'abc']
        mock_popen.assert_called_with(cmd,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      universal_newlines=True)

        self.op._is_yarn_application_mode = True
        with mock.patch(
                "ai_flow.operators.flink.flink_operator.FlinkOperator._retrieve_job_id_in_application_mode"
        ) as mock_retrive:
            self.op.stop(Context())
            cmd = ['flink', 'cancel', "-t", "yarn-application", "-Dyarn.application.id=app_id", 'abc']
            mock_popen.assert_called_with(cmd,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE,
                                          universal_newlines=True)
            mock_retrive.assert_called_once()

        self.op._is_yarn_per_job = True
        self.op.stop(Context())
        mock_popen.assert_called_with(['flink', 'cancel', '-yid', 'app_id', 'abc'],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      universal_newlines=True)

    def test__validate_parameters(self):
        self.op._target = 'yarn-per-job'
        self.op._validate_parameters()
        self.assertTrue(self.op._is_yarn_per_job)

        self.op._target = 'invalid'
        with self.assertRaisesRegex(AIFlowException, r'Invalid --target option'):
            self.op._validate_parameters()

        self.op._application_mode = True
        self.op._target = 'yarn-application'
        self.op._validate_parameters()
        self.assertTrue(self.op._is_yarn_application_mode)

        self.op._target = 'remote'
        with self.assertRaisesRegex(AIFlowException, r'Invalid --target option'):
            self.op._validate_parameters()

    def test__build_flink_command(self):
        self.op._target = 'whatever'
        self.op._kubernetes_cluster_id = 'deployment_id'
        self.op._is_kubernetes_session = True
        self.assertEqual(['/usr/bin/flink',
                          'run',
                          '--target', 'whatever',
                          '-Dkubernetes.cluster-id=deployment_id',
                          '-Dfoo=bar',
                          './flink-examples.jar',
                          '1000'],
                         self.op._build_flink_command())

        self.op._application_mode = True
        self.assertEqual(['/usr/bin/flink',
                          'run-application',
                          '--target', 'whatever',
                          '-Dkubernetes.cluster-id=deployment_id',
                          '-Dfoo=bar',
                          './flink-examples.jar', '1000'],
                         self.op._build_flink_command())

    @mock.patch('os.path.exists')
    @mock.patch('shutil.which')
    def test__get_executable_path(self, mock_which, mock_exists):
        with unittest.mock.patch.dict('os.environ', FLINK_HOME=os.path.dirname(__file__)):
            self.op._executable_path = None
            mock_exists.return_value = True
            mock_which.return_value = None
            self.assertEqual(os.path.join(os.path.dirname(__file__), 'bin/flink'),
                             self.op._get_executable_path())

    @mock.patch('subprocess.Popen')
    def test__start_tracking_yarn_application_status(self, mock_popen):
        with self.assertRaisesRegex(AIFlowException, "Yarn application id has not been obtained."):
            self.op._start_tracking_yarn_application_status()
        mock_popen.return_value.stdout = ['Final-State: FINISHED']
        mock_popen.return_value.wait.return_value = 0
        self.op._yarn_application_id = 'app_id'
        self.op._start_tracking_yarn_application_status()
        self.assertEqual('FINISHED', self.op._yarn_application_final_status)

    @mock.patch('ai_flow.operators.flink.flink_operator.FlinkOperator._list_jobs')
    @mock.patch('ai_flow.operators.flink.flink_operator.FlinkOperator._delete_cluster_in_k8s_application')
    def test__start_tracking_k8s_application_status(self, mock_delete, mock_list):
        mock_list.return_value = ["03.08.2022 17:15:27 : f6279216c6abac7045eb64514bcd4cb6"
                                  " : Flink Java Job at Wed Aug 03 09:15:25 UTC 2022 (FINISHED)"]
        self.op._start_tracking_k8s_application_status()
        self.assertEqual("FINISHED", self.op._k8s_application_job_status)
        mock_delete.assert_called_once()

    @mock.patch('subprocess.Popen')
    @mock.patch("ai_flow.operators.flink.flink_operator.FlinkOperator._get_executable_path")
    def test__list_jobs(self, mock_executable, mock_popen):
        mock_executable.return_value = 'flink'
        mock_popen.return_value.wait.return_value = 0
        self.op._kubernetes_cluster_id = 'deployment_id'
        self.op._yarn_application_id = 'app_id'

        self.op._is_kubernetes_application_mode = True
        self.op._list_jobs()
        cmd = ["flink", 'list', '-a', '-t', 'kubernetes-application', f'-Dkubernetes.cluster-id=deployment_id']
        mock_popen.assert_called_with(cmd,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      bufsize=-1,
                                      universal_newlines=True, )

        self.op._is_yarn_application_mode = True
        self.op._list_jobs()
        cmd = ["flink", 'list', '-a', '-t', 'yarn-application', f'-Dyarn.application.id=app_id']
        mock_popen.assert_called_with(cmd,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      bufsize=-1,
                                      universal_newlines=True,)

    @mock.patch('ai_flow.operators.flink.flink_operator.FlinkOperator._list_jobs')
    def test__retrieve_job_id_in_application_mode(self, mock_list):
        mock_list.return_value = ["03.08.2022 17:15:27 : f6279216c6abac7045eb64514bcd4cb6"
                                  " : Flink Java Job at Wed Aug 03 09:15:25 UTC 2022 (FINISHED)"]
        self.op._retrieve_job_id_in_application_mode()
        self.assertEqual('f6279216c6abac7045eb64514bcd4cb6', self.op._flink_job_id)

    def test__process_flink_run_log(self):
        logs = ['Job has been submitted with JobID f6279216c6abac7045eb64514bcd4cb6',
                '...',
                'yarn application_1658663952061_0020.']
        self.op._process_flink_run_log(logs)
        self.assertEqual('f6279216c6abac7045eb64514bcd4cb6', self.op._flink_job_id)
        self.assertEqual('application_1658663952061_0020', self.op._yarn_application_id)
