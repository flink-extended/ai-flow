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

import os
import unittest

import grpc

from ai_flow.api import ai_flow_context
from ai_flow.api.ai_flow_context import init_ai_flow_context, init_notebook_context
from ai_flow.context.project_context import current_project_context, current_project_config
from ai_flow.context.workflow_config_loader import current_workflow_config
from ai_flow.endpoint.server.server import AIFlowServer
from ai_flow.test.util.notification_service_utils import start_notification_server, stop_notification_server
from ai_flow.test.util.server_util import wait_for_server_started

_SQLITE_DB_FILE = 'aiflow.db'
_SQLITE_DB_URI = '%s%s' % ('sqlite:///', _SQLITE_DB_FILE)
_PORT = '50051'


class TestAIFlowContext(unittest.TestCase):
    def setUp(self):
        self.ns_server = start_notification_server()
        if os.path.exists(_SQLITE_DB_FILE):
            os.remove(_SQLITE_DB_FILE)
        self.server = AIFlowServer(store_uri=_SQLITE_DB_URI, port=_PORT,
                                   start_meta_service=True,
                                   start_metric_service=False,
                                   start_model_center_service=False,
                                   start_scheduler_service=False)
        self.server.run()
        wait_for_server_started('localhost:{}'.format(_PORT))

    def tearDown(self):
        self.server.stop()
        if os.path.exists(_SQLITE_DB_FILE):
            os.remove(_SQLITE_DB_FILE)
        stop_notification_server(self.ns_server)
        ai_flow_context.__init_notebook_context_flag__ = False
        ai_flow_context.__init_client_flag__ = False
        ai_flow_context.__init_context_flag__ = False

    def test_init_ai_flow_context(self):
        init_ai_flow_context()
        project_config = current_project_config()
        self.assertEqual('test_project', project_config.get_project_name())
        self.assertEqual('a', project_config.get('a'))
        project_context = current_project_context()
        self.assertEqual('test_project', project_context.project_name)
        workflow_config = current_workflow_config()
        self.assertEqual('test_ai_flow_context', workflow_config.workflow_name)
        self.assertEqual(5, len(workflow_config.job_configs))

        init_ai_flow_context()
        project_config = current_project_config()
        self.assertEqual('test_project', project_config.get_project_name())

        with self.assertRaises(Exception):
            init_notebook_context(project_config, workflow_config)


if __name__ == '__main__':
    unittest.main()
