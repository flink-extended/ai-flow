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
#
import os
import unittest

import ai_flow as af
from ai_flow.api import ai_flow_context
from ai_flow.api.ai_flow_context import init_ai_flow_context, init_notebook_context
from ai_flow.context.project_context import current_project_config, current_project_context
from ai_flow.context.workflow_config_loader import current_workflow_config
from ai_flow.endpoint.server.server import AIFlowServer
from ai_flow.project.project_config import ProjectConfig
from ai_flow.store.db.base_model import base
from ai_flow.test.store.test_sqlalchemy_store import _get_store
from ai_flow.test.util.notification_service_utils import start_notification_server, stop_notification_server, _NS_URI
from ai_flow.test.util.server_util import wait_for_server_started
from ai_flow.util import sqlalchemy_db
from ai_flow.workflow.job_config import JobConfig
from ai_flow.workflow.workflow_config import WorkflowConfig

_SQLITE_DB_FILE = 'aiflow.db'
_SQLITE_DB_URI = '%s%s' % ('sqlite:///', _SQLITE_DB_FILE)
_PORT = '50051'


class TestAIFlowContext(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        print("TestAIFlowContext setUpClass")
        cls.ns_server = start_notification_server()
        if os.path.exists(_SQLITE_DB_FILE):
            os.remove(_SQLITE_DB_FILE)
        cls.server = AIFlowServer(store_uri=_SQLITE_DB_URI, port=_PORT, start_scheduler_service=False)
        cls.server.run()
        wait_for_server_started('localhost:{}'.format(_PORT))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.stop()
        os.remove(_SQLITE_DB_FILE)
        stop_notification_server(cls.ns_server)

    def setUp(self) -> None:
        _get_store(_SQLITE_DB_URI)

    def tearDown(self) -> None:
        sqlalchemy_db.clear_db(_SQLITE_DB_URI, base.metadata)
        ai_flow_context.__init_context_flag__ = False
        ai_flow_context.__init_notebook_context_flag__ = False
        ai_flow_context.__init_client_flag__ = False

    def test_init_notebook_context(self):
        project_config: ProjectConfig = ProjectConfig()
        project_config.set_project_name('test_project')
        project_config.set_server_uri('localhost:50051')
        project_config.set_notification_server_uri('localhost:50052')
        project_config['blob'] = {
            'blob_manager_class': 'ai_flow.test.api.mock_plugins.MockBlobManger'}
        project_config['a'] = 'a'

        workflow_config: WorkflowConfig = WorkflowConfig('test_notebook_context')
        workflow_config.add_job_config('task_1', JobConfig(job_name='task_1', job_type='mock'))
        workflow_config.add_job_config('task_2', JobConfig(job_name='task_2', job_type='mock'))
        init_notebook_context(project_config, workflow_config)
        self.assertEqual('test_project', current_project_config().get_project_name())
        self.assertEqual('a', current_project_config().get('a'))
        self.assertEqual('test_project', current_project_context().project_name)
        self.assertEqual('test_notebook_context', current_workflow_config().workflow_name)
        self.assertEqual(2, len(current_workflow_config().job_configs))

        init_notebook_context(project_config, workflow_config)
        self.assertEqual('test_project', current_project_config().get_project_name())

        with self.assertRaises(Exception):
            init_ai_flow_context()

    def test_init_ai_client(self):
        af.init_ai_flow_client(server_uri='localhost:50051', project_name='test', notification_server_uri=_NS_URI)
        project_meta = af.get_project_by_name('test')
        self.assertEqual('test', project_meta.name)

    def test_init_ai_client_no_project_name(self):
        af.init_ai_flow_client(server_uri='localhost:50051', project_name=None, notification_server_uri=_NS_URI)
        project_meta = af.get_project_by_name('Unknown')
        self.assertEqual('Unknown', project_meta.name)

    def test_init_ai_client_register_dataset(self):
        af.init_ai_flow_client(server_uri='localhost:50051', project_name=None, notification_server_uri=_NS_URI)
        af.register_dataset(name='test_dataset', uri='/test')
        dataset_meta = af.get_dataset_by_name('test_dataset')
        self.assertEqual('/test', dataset_meta.uri)


if __name__ == '__main__':
    unittest.main()
