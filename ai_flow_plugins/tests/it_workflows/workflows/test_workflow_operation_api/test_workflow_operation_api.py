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
import unittest
import os
import time
import shutil
from typing import List

from airflow.models.dagrun import DagRun
from airflow.models.taskexecution import TaskExecution
from airflow.utils.session import create_session
from notification_service.base_notification import BaseEvent
from notification_service.client import NotificationClient

from ai_flow import AIFlowServerRunner, init_ai_flow_context
from ai_flow.workflow.status import Status
from ai_flow_plugins.job_plugins import python
import ai_flow as af
from ai_flow_plugins.job_plugins.python.python_processor import ExecutionContext
from ai_flow_plugins.tests.airflow_scheduler_utils import run_ai_flow_workflow, get_dag_id, get_workflow_execution_info, \
    set_workflow_execution_info
from ai_flow_plugins.tests import airflow_db_utils
from ai_flow.test.util.notification_service_utils import start_notification_server, stop_notification_server

project_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


class PyProcessor1(python.PythonProcessor):

    def process(self, execution_context: ExecutionContext, input_list: List) -> List:
        print("Zhang san hello world!")
        return []


class TestWorkflowOperationAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ns_server = start_notification_server()
        config_file = project_path + '/master.yaml'
        cls.master = AIFlowServerRunner(config_file=config_file)
        cls.master.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.master.stop()
        stop_notification_server(cls.ns_server)

    def setUp(self):
        airflow_db_utils.clear_all()
        self.master._clear_db()
        af.current_graph().clear_graph()
        init_ai_flow_context()

    def tearDown(self):
        self.master._clear_db()
        generated = '{}/generated'.format(project_path)
        if os.path.exists(generated):
            shutil.rmtree(generated)
        temp = '/tmp/aiflow'
        if os.path.exists(temp):
            shutil.rmtree(temp)

    def test_stop_and_resume_scheduling_job(self):
        def run_workflow(client: NotificationClient):
            with af.job_config('task_1'):
                af.user_define_operation(processor=PyProcessor1())
            af.action_on_event(job_name='task_1',
                               event_key='a',
                               event_value='a',
                               event_type='a',
                               sender='*',
                               namespace='*',
                               action=af.JobAction.RESTART)
            w = af.workflow_operation.submit_workflow(
                workflow_name=af.current_workflow_config().workflow_name)
            wei = af.workflow_operation.start_new_workflow_execution(
                workflow_name=af.current_workflow_config().workflow_name)
            set_workflow_execution_info(wei)
            # start the workflow execution
            while True:
                with create_session() as session:
                    dag_run = session.query(DagRun) \
                        .filter(DagRun.dag_id == 'test_project.{}'
                                .format(af.current_workflow_config().workflow_name)).first()
                    if dag_run is not None:
                        break
                    else:
                        time.sleep(1)

            client.send_event(BaseEvent(key='a', value='a', event_type='a'))
            time.sleep(5)
            af.workflow_operation.stop_scheduling_job(execution_id=wei.workflow_execution_id, job_name='task_1')
            client.send_event(BaseEvent(key='a', value='a', event_type='a'))
            time.sleep(5)
            af.workflow_operation.resume_scheduling_job(execution_id=wei.workflow_execution_id, job_name='task_1')
            client.send_event(BaseEvent(key='a', value='a', event_type='a'))
            while True:
                with create_session() as session:
                    task_executions = session.query(TaskExecution) \
                        .filter(TaskExecution.dag_id == 'test_project.{}'
                                .format(af.current_workflow_config().workflow_name),
                                TaskExecution.task_id == 'task_1').all()
                    if task_executions is not None and len(task_executions) > 1:
                        break
                    else:
                        time.sleep(1)

        run_ai_flow_workflow(dag_id=get_dag_id(af.current_project_config().get_project_name(),
                                               af.current_workflow_config().workflow_name),
                             test_function=run_workflow)

        job_execution_info_list = af.workflow_operation.list_job_executions(execution_id=get_workflow_execution_info().
                                                                            workflow_execution_id)
        self.assertEqual(2, len(job_execution_info_list))
        self.assertEqual(Status.FINISHED, job_execution_info_list[0].status)


if __name__ == '__main__':
    unittest.main()
