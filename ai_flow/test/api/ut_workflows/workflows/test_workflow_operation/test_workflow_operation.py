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
import shutil
import unittest
import os
from ai_flow.ai_graph.ai_graph import current_graph
from ai_flow.ai_graph.ai_node import AINode
from ai_flow.endpoint.server.server import AIFlowServer
from ai_flow.api.ai_flow_context import init_ai_flow_context
from ai_flow.context.workflow_config_loader import current_workflow_config
from ai_flow.api import workflow_operation, ai_flow_context
from ai_flow.scheduler_service.service.config import SchedulerServiceConfig
from ai_flow.test.util.notification_service_utils import start_notification_server, stop_notification_server
from ai_flow.test.util.server_util import wait_for_server_started

_SQLITE_DB_FILE = 'aiflow.db'
_SQLITE_DB_URI = '%s%s' % ('sqlite:///', _SQLITE_DB_FILE)
_PORT = '50051'


SCHEDULER_CLASS = 'ai_flow.test.api.mock_plugins.MockScheduler'
TEMP_DIR = '/tmp/ai_flow_mock_blob_directory'


class TestWorkflowOperation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns_server = start_notification_server()
        if os.path.exists(_SQLITE_DB_FILE):
            os.remove(_SQLITE_DB_FILE)
        raw_config = {
            'scheduler': {
                'scheduler_class': SCHEDULER_CLASS,
            }
        }
        config = SchedulerServiceConfig(raw_config)
        cls.server = AIFlowServer(store_uri=_SQLITE_DB_URI, port=_PORT,
                                  start_meta_service=True,
                                  start_metric_service=False,
                                  start_model_center_service=False,
                                  start_scheduler_service=True,
                                  scheduler_service_config=config)
        cls.server.run()
        wait_for_server_started('localhost:{}'.format(_PORT))
        if not os.path.exists(TEMP_DIR):
            os.makedirs(TEMP_DIR)

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
        if os.path.exists(_SQLITE_DB_FILE):
            os.remove(_SQLITE_DB_FILE)
        stop_notification_server(cls.ns_server)
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)

    def setUp(self):
        init_ai_flow_context()
        self.build_ai_graph()

    def tearDown(self):
        current_graph().clear_graph()

    def build_ai_graph(self):
        g = current_graph()
        for jc in current_workflow_config().job_configs.values():
            n = AINode(name=jc.job_name)
            n.config = jc
            g.add_node(n)

    def test_submit_workflow(self):
        w = workflow_operation.submit_workflow(workflow_name=current_workflow_config().workflow_name)
        self.assertEqual('test_workflow_operation', w.workflow_name)

    def test_delete_workflow(self):
        w = workflow_operation.submit_workflow(workflow_name=current_workflow_config().workflow_name)
        w = workflow_operation.delete_workflow(workflow_name=current_workflow_config().workflow_name)
        self.assertEqual('test_workflow_operation', w.workflow_name)

    def test_get_workflow(self):
        w = workflow_operation.submit_workflow(workflow_name=current_workflow_config().workflow_name)
        w = workflow_operation.get_workflow(workflow_name=current_workflow_config().workflow_name)
        self.assertEqual('test_workflow_operation', w.workflow_name)

    def test_list_workflows(self):
        w = workflow_operation.submit_workflow(workflow_name=current_workflow_config().workflow_name)
        w_list = workflow_operation.list_workflows(page_size=5, offset=0)
        self.assertEqual(1, len(w_list))
        self.assertEqual('test_workflow_operation', w_list[0].workflow_name)

    def test_pause_workflow(self):

        w = workflow_operation.pause_workflow_scheduling(workflow_name='workflow_1')
        self.assertEqual('workflow_1', w.workflow_name)

    def test_resume_workflow(self):

        w = workflow_operation.resume_workflow_scheduling(workflow_name='workflow_1')
        self.assertEqual('workflow_1', w.workflow_name)

    def test_start_new_workflow_execution(self):

        w = workflow_operation.start_new_workflow_execution(workflow_name='workflow_1')
        self.assertEqual('1', w.workflow_execution_id)

    def test_kill_all_workflow_execution(self):

        ws = workflow_operation.stop_all_workflow_executions(workflow_name='workflow_1')
        self.assertEqual(2, len(ws))

    def test_kill_workflow_execution(self):

        w = workflow_operation.stop_workflow_execution(execution_id='1')
        self.assertEqual('1', w.workflow_execution_id)

    def test_get_workflow_execution(self):

        w = workflow_operation.get_workflow_execution(execution_id='1')
        self.assertEqual('1', w.workflow_execution_id)

    def test_list_workflow_executions(self):

        ws = workflow_operation.list_workflow_executions(workflow_name='workflow_1')
        self.assertEqual(2, len(ws))

    def test_start_job_execution(self):

        j = workflow_operation.start_job_execution(job_name='task_1', execution_id='1')
        self.assertEqual('task_1', j.job_name)

    def test_stop_job_execution(self):

        j = workflow_operation.stop_job_execution(job_name='task_1', execution_id='1')
        self.assertEqual('task_1', j.job_name)

    def test_restart_job_execution(self):

        j = workflow_operation.restart_job_execution(job_name='task_1', execution_id='1')
        self.assertEqual('task_1', j.job_name)

    def test_get_job_execution(self):

        j = workflow_operation.get_job_executions(job_name='task_1', execution_id='1')
        self.assertEqual('task_1', j[0].job_name)
        self.assertEqual('test_label', j[0].execution_label)

    def test_list_job_execution(self):

        js = workflow_operation.list_job_executions(execution_id='1')
        self.assertEqual(2, len(js))

    def test_stop_scheduling_job(self):
        error = False
        try:
            workflow_operation.stop_scheduling_job(execution_id='1', job_name='task_1')
        except Exception:
            error = True
        self.assertFalse(error)

    def test_resume_scheduling_job(self):
        error = False
        try:
            workflow_operation.resume_scheduling_job(execution_id='1', job_name='task_1')
        except Exception:
            error = True
        self.assertFalse(error)


if __name__ == '__main__':
    unittest.main()
