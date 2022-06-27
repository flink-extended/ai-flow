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
import time
import unittest
from unittest import mock

from ai_flow.common.configuration import config_constants
from notification_service.embedded_notification_client import EmbeddedNotificationClient
from notification_service.event_storage import DbEventStorage
from notification_service.notification_client import NotificationClient
from notification_service.server import NotificationServer
from notification_service.service import NotificationService
from notification_service.util import db

from ai_flow.rpc.client.aiflow_client import get_ai_flow_client
from ai_flow.rpc.server.server import AIFlowServer
from ai_flow.sdk import operation
from tests.test_utils.unittest_base import BaseUnitTest


class OperationITest(BaseUnitTest):

    def setUp(self) -> None:
        if os.path.exists("/Users/alibaba/aiflow/.pid_registry.bak"):
            os.remove("/Users/alibaba/aiflow/.pid_registry.bak")
        if os.path.exists("/Users/alibaba/aiflow/.pid_registry.dat"):
            os.remove("/Users/alibaba/aiflow/.pid_registry.dat")
        if os.path.exists("/Users/alibaba/aiflow/.pid_registry.dir"):
            os.remove("/Users/alibaba/aiflow/.pid_registry.dir")

        super().setUp()
        self.ns_db_file = 'test_ns.db'
        self.start_notification_server()
        self.server = AIFlowServer()
        self.server.run(is_block=False)
        self.client = get_ai_flow_client()
        self.client.add_namespace('default')

    def tearDown(self) -> None:
        self.server.stop()
        self.stop_notification_server()
        super().tearDown()

    def test_upload_workflows(self):
        operation.upload_workflows(os.path.join(os.path.dirname(__file__), 'test_workflow.py'))
        operation.start_workflow_execution(workflow_name='workflow1', namespace='default')
        time.sleep(20)

    def start_notification_server(self):
        if os.path.exists('notification_service.db'):
            os.remove('notification_service.db')
        db.create_all_tables()
        db_conn = "sqlite:///notification_service.db"
        storage = DbEventStorage(db_conn)
        self.master = NotificationServer(NotificationService(storage), port='50052')
        self.master.run()
        self.wait_for_ns_started("localhost:50052")

    def stop_notification_server(self):
        self.master.stop()
        if os.path.exists('notification_service.db'):
            os.remove('notification_service.db')

    @staticmethod
    def wait_for_ns_started(server_uri):
        last_exception = None
        for i in range(60):
            try:
                return EmbeddedNotificationClient(server_uri=server_uri, namespace='default', sender='sender')
            except Exception as e:
                time.sleep(2)
                last_exception = e
        raise Exception("The server %s is unavailable." % server_uri) from last_exception
