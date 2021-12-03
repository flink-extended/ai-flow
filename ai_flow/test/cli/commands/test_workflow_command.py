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
from contextlib import redirect_stdout

from ai_flow import current_project_config
from ai_flow.cli.commands.workflow_command import workflow_delete, workflow_list, workflow_list_executions, \
    workflow_pause_scheduling, workflow_show, workflow_show_execution, workflow_resume_scheduling, \
    workflow_start_execution, workflow_stop_execution, workflow_stop_executions, workflow_submit
from ai_flow.context.workflow_config_loader import current_workflow_config
from ai_flow.test.cli.commands.ut_workflows.workflows.test_command.test_command import TestCommand, PROJECT_PATH


class TestCliWorkflow(TestCommand):

    def test_cli_workflow_delete(self):
        workflow_submit(
            self.parser.parse_args(['workflow', 'submit', PROJECT_PATH, current_workflow_config().workflow_name]))
        with redirect_stdout(io.StringIO()) as stdout:
            workflow_delete(
                self.parser.parse_args(
                    ['workflow', 'delete', PROJECT_PATH, current_workflow_config().workflow_name, '-y']))
        self.assertEquals('Workflow: {}, deleted: {}.'.format(current_workflow_config().workflow_name, True),
                          str.splitlines(stdout.getvalue())[0])

    def test_cli_workflow_list(self):
        workflow_submit(
            self.parser.parse_args(['workflow', 'submit', PROJECT_PATH, current_workflow_config().workflow_name]))
        with redirect_stdout(io.StringIO()) as stdout:
            workflow_list(
                self.parser.parse_args(['workflow', 'list', PROJECT_PATH]))
        self.assertEquals('{} | {}  | {}         | {}'.format(current_project_config().get_project_name(),
                                                              current_workflow_config().workflow_name, '{}', 'None'),
                          str.splitlines(stdout.getvalue())[2].strip())

    def test_cli_workflow_list_executions(self):
        with redirect_stdout(io.StringIO()) as stdout:
            workflow_list_executions(
                self.parser.parse_args(['workflow', 'list-executions', PROJECT_PATH, 'workflow_1']))
        self.assertEquals(11, len(str.splitlines(stdout.getvalue())))

    def test_cli_workflow_pause_scheduling(self):
        with redirect_stdout(io.StringIO()) as stdout:
            workflow_pause_scheduling(
                self.parser.parse_args(['workflow', 'pause-scheduling', PROJECT_PATH, 'workflow_1']))
        self.assertEquals('Workflow: {}, paused: {}.'.format('workflow_1', True),
                          str.splitlines(stdout.getvalue())[0])

    def test_cli_workflow_resume_scheduling(self):
        with redirect_stdout(io.StringIO()) as stdout:
            workflow_resume_scheduling(
                self.parser.parse_args(['workflow', 'resume-scheduling', PROJECT_PATH, 'workflow_1']))
        self.assertEquals('Workflow: {}, resumed: {}.'.format('workflow_1', True),
                          str.splitlines(stdout.getvalue())[0])

    def test_cli_workflow_show(self):
        workflow_submit(
            self.parser.parse_args(['workflow', 'submit', PROJECT_PATH, current_workflow_config().workflow_name]))
        with redirect_stdout(io.StringIO()) as stdout:
            workflow_show(
                self.parser.parse_args(['workflow', 'show', PROJECT_PATH, current_workflow_config().workflow_name]))
        self.assertEquals('{} | {}  | {}         | {}'.format(current_project_config().get_project_name(),
                                                              current_workflow_config().workflow_name, '{}', 'None'),
                          str.splitlines(stdout.getvalue())[2].strip())

    def test_cli_workflow_show_execution(self):
        with redirect_stdout(io.StringIO()) as stdout:
            workflow_show_execution(
                self.parser.parse_args(['workflow', 'show-execution', PROJECT_PATH, '1']))
        self.assertEquals(8, len(str.splitlines(stdout.getvalue())))

    def test_cli_workflow_start_execution(self):
        with redirect_stdout(io.StringIO()) as stdout:
            workflow_start_execution(
                self.parser.parse_args(['workflow', 'start-execution', PROJECT_PATH, 'workflow_1']))
        self.assertEquals('Workflow: {}, started: {}.'.format('workflow_1', True),
                          str.splitlines(stdout.getvalue())[0])

    def test_cli_workflow_stop_execution(self):
        with redirect_stdout(io.StringIO()) as stdout:
            workflow_stop_execution(
                self.parser.parse_args(['workflow', 'stop-execution', PROJECT_PATH, '1']))
        self.assertEquals('Workflow Execution: {}, stopped: {}.'.format('1', True),
                          str.splitlines(stdout.getvalue())[0])

    def test_cli_workflow_stop_executions(self):
        with redirect_stdout(io.StringIO()) as stdout:
            workflow_stop_executions(
                self.parser.parse_args(['workflow', 'stop-executions', PROJECT_PATH, 'workflow_1']))
        self.assertEquals('Workflow: {}, stopped: {}.'.format('workflow_1', True),
                          str.splitlines(stdout.getvalue())[0])

    def test_cli_workflow_submit(self):
        with redirect_stdout(io.StringIO()) as stdout:
            workflow_submit(
                self.parser.parse_args(['workflow', 'submit', PROJECT_PATH, current_workflow_config().workflow_name]))
        self.assertEquals('Workflow: {}, submitted: {}.\n'.format(current_workflow_config().workflow_name, True),
                          stdout.getvalue())
