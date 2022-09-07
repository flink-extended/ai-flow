#
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
#s
import time
import unittest


from ai_flow.client.ai_flow_client import AIFlowClient
from ai_flow.endpoint.server.server import AIFlowServer
from ai_flow.store.db.base_model import base
from ai_flow.store.sqlalchemy_store import SqlAlchemyStore
from ai_flow.util import sqlalchemy_db
from ai_flow.test.util.notification_service_utils import start_notification_server, stop_notification_server

_SQLITE_DB_FILE = 'aiflow.db'
_SQLITE_DB_URI = '%s%s' % ('sqlite:///', _SQLITE_DB_FILE)


@unittest.skip("Skip until HA is re-implemented.")
class TestHighAvailableAIFlowServer(unittest.TestCase):

    @staticmethod
    def start_aiflow_server(host, port):
        port = str(port)
        server_uri = host + ":" + port
        server = AIFlowServer(
            store_uri=_SQLITE_DB_URI, port=port, enabled_ha=True, start_scheduler_service=False,
            ha_server_uri=server_uri, notification_server_uri='localhost:30031')
        server.run()
        return server

    def wait_for_new_members_detected(self, new_member_uri):
        while True:
            living_member = self.client.living_aiflow_members
            if new_member_uri in living_member:
                break
            else:
                time.sleep(1)

    def setUp(self) -> None:
        SqlAlchemyStore(_SQLITE_DB_URI)
        self.ns_server = start_notification_server()
        self.server1 = AIFlowServer(
            store_uri=_SQLITE_DB_URI, port=50051, enabled_ha=True, start_scheduler_service=False,
            ha_server_uri='localhost:50051', notification_server_uri='localhost:30031')
        self.server1.run()
        self.server2 = None
        self.server3 = None
        self.client = AIFlowClient(server_uri='localhost:50051',
                                   enable_ha=True)

    def tearDown(self) -> None:
        self.client.disable_high_availability()
        if self.server1 is not None:
            self.server1.stop()
        if self.server2 is not None:
            self.server2.stop()
        if self.server3 is not None:
            self.server3.stop()

        sqlalchemy_db.clear_db(_SQLITE_DB_URI, base.metadata)
        stop_notification_server(self.ns_server)
        self.ns_server.storage.clean_up()

    def test_server_change(self) -> None:
        self.client.register_project("test_project")
        projects = self.client.list_projects(10, 0)
        self.assertEqual(self.client.current_aiflow_uri, "localhost:50051")
        self.assertEqual(projects[0].name, "test_project")

        self.server2 = self.start_aiflow_server("localhost", 50052)
        self.wait_for_new_members_detected("localhost:50052")
        self.server1.stop()
        projects = self.client.list_projects(10, 0)
        self.assertEqual(self.client.current_aiflow_uri, "localhost:50052")
        self.assertEqual(projects[0].name, "test_project")

        self.server3 = self.start_aiflow_server("localhost", 50053)
        self.wait_for_new_members_detected("localhost:50053")
        self.server2.stop()
        projects = self.client.list_projects(10, 0)
        self.assertEqual(self.client.current_aiflow_uri, "localhost:50053")
        self.assertEqual(projects[0].name, "test_project")
