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

from typing import Text, Optional, List

from ai_flow.context.project_context import ProjectContext
from ai_flow.plugin_interface.scheduler_interface import Scheduler, WorkflowExecutionInfo, WorkflowInfo, \
    JobExecutionInfo
from ai_flow.util import path_util
from ai_flow.workflow.workflow import Workflow

DEFAULT_MYSQL_USERNAME = ''
DEFAULT_MYSQL_PASSWORD = ''
DEFAULT_MYSQL_HOST = ''
DEFAULT_MYSQL_PORT = 3306

DEFAULT_MONGODB_USERNAME = ''
DEFAULT_MONGODB_PASSWORD = ''
DEFAULT_MONGODB_HOST = ''
DEFAULT_MONGODB_PORT = 27017


def get_project_path():
    return os.path.dirname(os.path.abspath(__file__))


def get_project_config_file():
    return os.path.dirname(os.path.abspath(__file__)) + "/project.yaml"


def get_master_config_file():
    return os.path.dirname(os.path.abspath(__file__)) + "/master.yaml"


def get_workflow_config_file():
    return os.path.dirname(os.path.abspath(__file__)) + "/workflow_config.yaml"


def get_mysql_server_url():
    db_username = os.environ.get('MYSQL_TEST_USERNAME') if 'MYSQL_TEST_USERNAME' in os.environ \
        else DEFAULT_MYSQL_USERNAME
    db_password = os.environ.get('MYSQL_TEST_PASSWORD') if 'MYSQL_TEST_PASSWORD' in os.environ \
        else DEFAULT_MYSQL_PASSWORD
    db_host = str(os.environ['MYSQL_TEST_HOST']) if 'MYSQL_TEST_HOST' in os.environ \
        else DEFAULT_MYSQL_HOST
    db_port = int(os.environ['MYSQL_TEST_PORT']) if 'MYSQL_TEST_PORT' in os.environ \
        else DEFAULT_MYSQL_PORT
    if db_username is None or db_password is None:
        raise Exception(
            "Username and password for MySQL tests must be specified via the "
            "MYSQL_TEST_USERNAME and MYSQL_TEST_PASSWORD environment variables. "
            "environment variable. In posix shells, you rerun your test command "
            "with the environment variables set, e.g: MYSQL_TEST_USERNAME=your_username "
            "MYSQL_TEST_PASSWORD=your_password <your-test-command>. You may optionally "
            "specify MySQL host via MYSQL_TEST_HOST (default is 100.69.96.145) "
            "and specify MySQL port via MYSQL_TEST_PORT (default is 3306).")
    return 'mysql+pymysql://%s:%s@%s:%s' % (db_username, db_password, db_host, db_port)


def get_mongodb_server_url():
    db_username = os.environ.get('MONGODB_TEST_USERNAME') if 'MONGODB_TEST_USERNAME' in os.environ \
        else DEFAULT_MONGODB_USERNAME
    db_password = os.environ.get('MONGODB_TEST_PASSWORD') if 'MONGODB_TEST_PASSWORD' in os.environ \
        else DEFAULT_MONGODB_PASSWORD
    db_host = str(os.environ['MONGODB_TEST_HOST']) if 'MONGODB_TEST_HOST' in os.environ \
        else DEFAULT_MONGODB_HOST
    db_port = int(os.environ['MONGODB_TEST_PORT']) if 'MONGODB_TEST_PORT' in os.environ \
        else DEFAULT_MONGODB_PORT
    if db_username is None or db_password is None:
        raise Exception(
            "Username and password for MONGODB tests must be specified via the "
            "MONGODB_TEST_USERNAME and MONGODB_TEST_PASSWORD environment variables. "
            "environment variable. In posix shells, you rerun your test command "
            "with the environment variables set, e.g: MONGODB_TEST_USERNAME=your_username "
            "MONGODB_TEST_PASSWORD=your_password <your-test-command>. You may optionally "
            "specify MONGODB host via MONGODB_TEST_HOST and specify MONGODB port "
            "via MONGODB_TEST_PORT.")
    return 'mongodb://%s:%s@%s:%s' % (db_username, db_password, db_host, db_port)


class MockScheduler(Scheduler):
    def stop_scheduling_job(self, workflow_execution_id: Text, job_name: Text):
        pass

    def resume_scheduling_job(self, workflow_execution_id: Text, job_name: Text):
        pass

    def stop_workflow_execution_by_context(self, workflow_name: Text, context: Text) -> Optional[WorkflowExecutionInfo]:
        pass

    def delete_workflow(self, project_name: Text, workflow_name: Text) -> WorkflowInfo:
        pass

    def start_job_execution(self, job_name: Text, workflow_execution_id: Text) -> JobExecutionInfo:
        pass

    def stop_job_execution(self, job_name: Text, workflow_execution_id: Text) -> JobExecutionInfo:
        pass

    def restart_job_execution(self, job_name: Text, workflow_execution_id: Text) -> JobExecutionInfo:
        pass

    def get_job_executions(self, job_name: Text, workflow_execution_id: Text) -> List[JobExecutionInfo]:
        pass

    def list_job_executions(self, workflow_execution_id: Text) -> List[JobExecutionInfo]:
        pass

    def submit_workflow(self, workflow: Workflow, context_extractor, project_context: ProjectContext) -> WorkflowInfo:
        pass

    def pause_workflow_scheduling(self, project_name: Text, workflow_name: Text) -> WorkflowInfo:
        pass

    def resume_workflow_scheduling(self, project_name: Text, workflow_name: Text) -> WorkflowInfo:
        pass

    def start_new_workflow_execution(self, project_name: Text, workflow_name: Text, context: Text = None) \
            -> WorkflowExecutionInfo:
        pass

    def stop_all_workflow_execution(self, project_name: Text, workflow_name: Text) -> List[WorkflowExecutionInfo]:
        pass

    def stop_workflow_execution(self, workflow_execution_id: Text) -> WorkflowExecutionInfo:
        pass

    def get_workflow_execution(self, workflow_execution_id: Text) -> WorkflowExecutionInfo:
        pass

    def list_workflow_executions(self, project_name: Text, workflow_name: Text) -> List[WorkflowExecutionInfo]:
        pass


MOCK_SCHEDULER_CLASS = 'ai_flow.test.test_util.MockScheduler'
