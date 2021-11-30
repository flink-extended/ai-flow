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

import io
import os
import unittest
from contextlib import redirect_stdout

from ai_flow import current_project_config
from ai_flow.ai_graph.ai_graph import current_graph
from ai_flow.ai_graph.ai_node import AINode
from ai_flow.api.ai_flow_context import init_ai_flow_context
from ai_flow.cli import cli_parser
from ai_flow.cli.commands.workflow_command import workflow_delete, workflow_list, workflow_list_executions, \
    workflow_pause_scheduling, workflow_show, workflow_show_execution, workflow_resume_scheduling, \
    workflow_start_execution, workflow_stop_execution, workflow_stop_executions, workflow_submit
from ai_flow.context.workflow_config_loader import current_workflow_config
from ai_flow.endpoint.server.server import AIFlowServer
from ai_flow.scheduler_service.service.config import SchedulerServiceConfig
from ai_flow.test.util.notification_service_utils import start_notification_server, stop_notification_server
from ai_flow.util.path_util import get_file_dir, get_parent_dir

_SQLITE_DB_FILE = 'aiflow.db'
_SQLITE_DB_URI = '%s%s' % ('sqlite:///', _SQLITE_DB_FILE)
_PORT = '50051'
_SERVER_URI = 'localhost:{}'.format(_PORT)
_SCHEDULER_CLASS = 'ai_flow.test.api.mock_plugins.MockScheduler'
_WORKFLOW_NAME = 'test_workflow_operation'
_PROJECT_PATH = get_parent_dir(get_parent_dir(get_file_dir(__file__)))


class TestCliWorkflow(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.parser = cli_parser.get_parser()
        cls.notification_server = start_notification_server()
        if os.path.exists(_SQLITE_DB_FILE):
            os.remove(_SQLITE_DB_FILE)
        raw_config = {
            'scheduler': {
                'scheduler_class': _SCHEDULER_CLASS,
            }
        }
        config = SchedulerServiceConfig(raw_config)
        cls.aiflow_server = AIFlowServer(store_uri=_SQLITE_DB_URI, port=_PORT,
                                         start_meta_service=True,
                                         start_metric_service=False,
                                         start_model_center_service=False,
                                         start_scheduler_service=True,
                                         scheduler_service_config=config)
        cls.aiflow_server.run()
        init_ai_flow_context()

    @classmethod
    def tearDownClass(cls):
        cls.aiflow_server.stop()
        if os.path.exists(_SQLITE_DB_FILE):
            os.remove(_SQLITE_DB_FILE)
        stop_notification_server(cls.notification_server)

    def setUp(self):
        self.build_ai_graph()

    def tearDown(self):
        current_graph().clear_graph()

    @classmethod
    def build_ai_graph(cls):
        graph = current_graph()
        for job_config in current_workflow_config().job_configs.values():
            node = AINode(name=job_config.job_name)
            node.config = job_config
            graph.add_node(node)

    def test_cli_workflow_delete(self):
        workflow_submit(
            self.parser.parse_args(['workflow', 'submit', _PROJECT_PATH, current_workflow_config().workflow_name]))
        with redirect_stdout(io.StringIO()) as stdout:
            workflow_delete(
                self.parser.parse_args(
                    ['workflow', 'delete', _PROJECT_PATH, current_workflow_config().workflow_name, '-y']))
        self.assertEquals('Workflow: {}, deleted: {}.'.format(current_workflow_config().workflow_name, True),
                          str.splitlines(stdout.getvalue())[0])

    def test_cli_workflow_list(self):
        workflow_submit(
            self.parser.parse_args(['workflow', 'submit', _PROJECT_PATH, current_workflow_config().workflow_name]))
        with redirect_stdout(io.StringIO()) as stdout:
            workflow_list(
                self.parser.parse_args(['workflow', 'list', _PROJECT_PATH]))
        self.assertEquals('{} | {} | {}         | {}'.format(current_project_config().get_project_name(),
                                                             current_workflow_config().workflow_name, '{}', 'None'),
                          str.splitlines(stdout.getvalue())[2].strip())

    def test_cli_workflow_list_executions(self):
        with redirect_stdout(io.StringIO()) as stdout:
            workflow_list_executions(
                self.parser.parse_args(['workflow', 'list-executions', _PROJECT_PATH, 'workflow_1']))
        self.assertEquals(11, len(str.splitlines(stdout.getvalue())))

    def test_cli_workflow_pause_scheduling(self):
        with redirect_stdout(io.StringIO()) as stdout:
            workflow_pause_scheduling(
                self.parser.parse_args(['workflow', 'pause-scheduling', _PROJECT_PATH, 'workflow_1']))
        self.assertEquals('Workflow: {}, paused: {}.'.format('workflow_1', True),
                          str.splitlines(stdout.getvalue())[0])

    def test_cli_workflow_resume_scheduling(self):
        with redirect_stdout(io.StringIO()) as stdout:
            workflow_resume_scheduling(
                self.parser.parse_args(['workflow', 'resume-scheduling', _PROJECT_PATH, 'workflow_1']))
        self.assertEquals('Workflow: {}, resumed: {}.'.format('workflow_1', True),
                          str.splitlines(stdout.getvalue())[0])

    def test_cli_workflow_show(self):
        workflow_submit(
            self.parser.parse_args(['workflow', 'submit', _PROJECT_PATH, current_workflow_config().workflow_name]))
        with redirect_stdout(io.StringIO()) as stdout:
            workflow_show(
                self.parser.parse_args(['workflow', 'show', _PROJECT_PATH, current_workflow_config().workflow_name]))
        self.assertEquals('{} | {} | {}         | {}'.format(current_project_config().get_project_name(),
                                                             current_workflow_config().workflow_name, '{}', 'None'),
                          str.splitlines(stdout.getvalue())[2].strip())

    def test_cli_workflow_show_execution(self):
        with redirect_stdout(io.StringIO()) as stdout:
            workflow_show_execution(
                self.parser.parse_args(['workflow', 'show-execution', _PROJECT_PATH, '1']))
        self.assertEquals(8, len(str.splitlines(stdout.getvalue())))

    def test_cli_workflow_start_execution(self):
        with redirect_stdout(io.StringIO()) as stdout:
            workflow_start_execution(
                self.parser.parse_args(['workflow', 'start-execution', _PROJECT_PATH, 'workflow_1']))
        self.assertEquals('Workflow: {}, started: {}.'.format('workflow_1', True),
                          str.splitlines(stdout.getvalue())[0])

    def test_cli_workflow_stop_execution(self):
        with redirect_stdout(io.StringIO()) as stdout:
            workflow_stop_execution(
                self.parser.parse_args(['workflow', 'stop-execution', _PROJECT_PATH, '1']))
        self.assertEquals('Workflow Execution: {}, stopped: {}.'.format('1', True),
                          str.splitlines(stdout.getvalue())[0])

    def test_cli_workflow_stop_executions(self):
        with redirect_stdout(io.StringIO()) as stdout:
            workflow_stop_executions(
                self.parser.parse_args(['workflow', 'stop-executions', _PROJECT_PATH, 'workflow_1']))
        self.assertEquals('Workflow: {}, stopped: {}.'.format('workflow_1', True),
                          str.splitlines(stdout.getvalue())[0])

    def test_cli_workflow_submit(self):
        with redirect_stdout(io.StringIO()) as stdout:
            workflow_submit(
                self.parser.parse_args(['workflow', 'submit', _PROJECT_PATH, current_workflow_config().workflow_name]))
        self.assertEquals('Workflow: {}, submitted: {}.\n'.format(current_workflow_config().workflow_name, True),
                          stdout.getvalue())
