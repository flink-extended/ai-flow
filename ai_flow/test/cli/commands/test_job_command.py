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

from ai_flow.cli.commands.job_command import job_list_executions, job_restart_execution, job_show_execution, \
    job_start_execution, job_stop_execution, job_stop_scheduling, job_resume_scheduling
from ai_flow.test.cli.commands.test_command import TestCommand, PROJECT_PATH


class TestCliJob(TestCommand):

    def test_cli_job_list_executions(self):
        with redirect_stdout(io.StringIO()) as stdout:
            job_list_executions(
                self.parser.parse_args(['job', 'list-executions', PROJECT_PATH, '1']))
        self.assertEquals(8, len(str.splitlines(stdout.getvalue())[0].split('|')))

    def test_cli_job_restart_execution(self):
        with redirect_stdout(io.StringIO()) as stdout:
            job_restart_execution(
                self.parser.parse_args(['job', 'restart-execution', PROJECT_PATH, 'task_1', '1']))
        self.assertEquals('Job: {}, workflow execution: {}, restarted: {}.'.format('task_1', '1', True),
                          str.splitlines(stdout.getvalue())[0])

    def test_cli_job_show_execution(self):
        with redirect_stdout(io.StringIO()) as stdout:
            job_show_execution(
                self.parser.parse_args(['job', 'show-execution', PROJECT_PATH, 'task_1', '1']))
        self.assertEquals(8, len(str.splitlines(stdout.getvalue())[0].split('|')))

    def test_cli_job_start_execution(self):
        with redirect_stdout(io.StringIO()) as stdout:
            job_start_execution(
                self.parser.parse_args(['job', 'start-execution', PROJECT_PATH, 'task_1', '1']))
        self.assertEquals('Job: {}, workflow execution: {}, started: {}.'.format('task_1', '1', True),
                          str.splitlines(stdout.getvalue())[0])

    def test_cli_job_stop_execution(self):
        with redirect_stdout(io.StringIO()) as stdout:
            job_stop_execution(
                self.parser.parse_args(['job', 'stop-execution', PROJECT_PATH, 'task_1', '1']))
        self.assertEquals('Job: {}, workflow execution: {}, stopped: {}.'.format('task_1', '1', True),
                          str.splitlines(stdout.getvalue())[0])

    def test_cli_job_stop_scheduling(self):
        with redirect_stdout(io.StringIO()) as stdout:
            job_stop_scheduling(
                self.parser.parse_args(['job', 'stop-scheduling', PROJECT_PATH, 'task_1', '1']))
        self.assertTrue("stop scheduling" in stdout.getvalue())

    def test_cli_job_resume_scheduling(self):
        with redirect_stdout(io.StringIO()) as stdout:
            job_resume_scheduling(
                self.parser.parse_args(['job', 'resume-scheduling', PROJECT_PATH, 'task_1', '1']))
        self.assertTrue("resume scheduling" in stdout.getvalue())
