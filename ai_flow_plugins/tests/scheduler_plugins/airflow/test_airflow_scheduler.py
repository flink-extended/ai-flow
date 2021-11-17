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
import logging
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

import cloudpickle

from ai_flow.api.context_extractor import BroadcastAllContextExtractor
from ai_flow.context.project_context import ProjectContext
from ai_flow.project.project_config import ProjectConfig
from ai_flow.workflow.workflow import Workflow
from ai_flow.workflow.workflow_config import WorkflowConfig
from ai_flow_plugins.scheduler_plugins.airflow.airflow_scheduler import AirFlowScheduler


class TestAirflowScheduler(unittest.TestCase):
    logger = logging.getLogger('TestAirflowScheduler')

    def setUp(self) -> None:
        self.temp_deploy_path = tempfile.TemporaryDirectory().name
        self.logger.info("temp airflow deploy path: {}".format(self.temp_deploy_path))
        self.scheduler = AirFlowScheduler({'airflow_deploy_path': self.temp_deploy_path,
                                           'notification_server_uri': 'localhost:50051'})
        self.scheduler._airflow_client = Mock()
        self.scheduler.dag_generator = Mock()

    def test_airflow_scheduler_without_dag_deploy_path(self):
        with patch("airflow.settings") as s:
            s.DAGS_FOLDER = 'test_folder'
            scheduler = AirFlowScheduler({'notification_server_uri': 'localhost:50051'})
            self.assertEqual('test_folder', scheduler.config['airflow_deploy_path'])

    def test_airflow_scheduler_submit_workflow(self):
        workflow_name = 'test_workflow'
        workflow = self._get_workflow(workflow_name)

        project_name = 'test_project'
        project_context = self._get_project_context(project_name)

        mock_generated_code = 'mock generated code'
        self.scheduler.dag_generator.generate.return_value = mock_generated_code

        context_extractor = BroadcastAllContextExtractor()
        self.scheduler.submit_workflow(workflow, context_extractor=context_extractor,
                                       project_context=project_context)

        dag_file_path = os.path.join(self.temp_deploy_path, '.'.join([project_name, workflow_name, 'py']))
        self.assertTrue(os.path.exists(dag_file_path))
        with open(dag_file_path, 'rt') as f:
            self.assertEqual(mock_generated_code, f.read())

    def test_airflow_scheduler_delete_workflow(self):
        workflow_name = 'test_workflow'
        workflow = self._get_workflow(workflow_name)

        project_name = 'test_project'
        project_context = self._get_project_context(project_name)

        mock_generated_code = 'mock generated code'
        self.scheduler.dag_generator.generate.return_value = mock_generated_code

        context_extractor = BroadcastAllContextExtractor()
        self.scheduler.submit_workflow(workflow, context_extractor=context_extractor,
                                       project_context=project_context)
        dag_file_path = os.path.join(self.temp_deploy_path, '.'.join([project_name, workflow_name, 'py']))
        self.assertTrue(os.path.exists(dag_file_path))

        with patch('ai_flow_plugins.scheduler_plugins.airflow.airflow_scheduler.'
                   'AirFlowScheduler.pause_workflow_scheduling') as pause_func:
            with patch('ai_flow_plugins.scheduler_plugins.airflow.airflow_scheduler.'
                       'AirFlowScheduler.stop_all_workflow_execution') as stop_func:
                with patch('airflow.api.common.experimental.delete_dag.delete_dag') as delete_func:
                    self.scheduler.delete_workflow(project_name, workflow_name)
        pause_func.assert_called_with(project_name=project_name, workflow_name=workflow_name)
        stop_func.assert_called_with(project_name=project_name, workflow_name=workflow_name)
        delete_func.assert_called_with('{}.{}'.format(project_name, workflow_name))
        self.assertFalse(os.path.exists(dag_file_path))

    def test_airflow_scheduler_submit_workflow_with_customized_context_extractor(self):
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'context_extractor_pickle_maker.py')
        os.system('python {}'.format(script_path))
        context_extractor_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                              'context_extractor.pickle')

        try:
            workflow_name = 'test_workflow_with_context_extractor'
            workflow = self._get_workflow(workflow_name)
            with open(context_extractor_path, 'rb') as f:
                context_extractor = cloudpickle.load(f)

            project_name = 'test_project'
            project_context = self._get_project_context(project_name)

            mock_generated_code = 'mock generated code'
            self.scheduler.dag_generator.generate.return_value = mock_generated_code

            self.scheduler.submit_workflow(workflow, context_extractor=context_extractor,
                                           project_context=project_context)

            dag_file_path = os.path.join(self.temp_deploy_path, '.'.join([project_name, workflow_name, 'py']))
            self.assertTrue(os.path.exists(dag_file_path))
            with open(dag_file_path, 'rt') as f:
                self.assertEqual(mock_generated_code, f.read())

        finally:
            os.remove(context_extractor_path)

    @staticmethod
    def _get_project_context(project_name):
        project_context: ProjectContext = ProjectContext()
        project_context.project_config = ProjectConfig()
        project_context.project_config.set_project_name(project_name)
        return project_context

    @staticmethod
    def _get_workflow(workflow_name):
        workflow = Workflow()
        workflow.workflow_config = WorkflowConfig(workflow_name=workflow_name)
        return workflow
