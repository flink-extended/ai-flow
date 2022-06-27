## Copyright 2022 The AI Flow Authors
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
import pickle
import time
from unittest import mock

from notification_service.embedded_notification_client import EmbeddedNotificationClient
from notification_service.event_storage import DbEventStorage
from notification_service.server import NotificationServer
from notification_service.service import NotificationService
from notification_service.util import db

from ai_flow.model.operators.bash import BashOperator
from ai_flow.model.workflow import Workflow
from ai_flow.rpc.client.aiflow_client import get_ai_flow_client
from ai_flow.rpc.server.server import AIFlowServer
from tests.test_utils.unittest_base import BaseUnitTest


class TestAIFlowServer(BaseUnitTest):
    def setUp(self) -> None:
        super().setUp()
        self.start_notification_server()
        self.server = AIFlowServer()
        self.server.run(is_block=False)
        self.client = get_ai_flow_client()

    def tearDown(self) -> None:
        self.server.stop()
        self.stop_notification_server()
        super().tearDown()

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

    def test_namespace_operation(self):
        namespace = self.client.add_namespace('ns1', {'key': 'value'})
        self.assertEqual('ns1', namespace.name)
        self.assertEqual({'key': 'value'}, namespace.get_properties())

        namespace = self.client.get_namespace('ns1')
        self.assertEqual('ns1', namespace.name)
        self.assertEqual({'key': 'value'}, namespace.get_properties())

        namespace = self.client.update_namespace('ns1', {'key2': 'value2'})
        self.assertEqual('ns1', namespace.name)
        self.assertEqual({'key2': 'value2'}, namespace.get_properties())

        self.client.add_namespace('ns2', {'key': 'value'})
        self.client.add_namespace('ns3', {'key': 'value'})
        namespaces = self.client.list_namespaces()
        self.assertEqual(3, len(namespaces))

        namespaces = self.client.list_namespaces(page_size=2, offset=1)
        self.assertEqual(2, len(namespaces))
        self.assertEqual('ns2', namespaces[0].name)
        self.assertEqual('ns3', namespaces[1].name)

        namespaces = self.client.list_namespaces(page_size=2, offset=2)
        self.assertEqual(1, len(namespaces))
        self.assertEqual('ns3', namespaces[0].name)

        self.assertFalse(self.client.delete_namespace('non-exists'))
        self.client.delete_namespace('ns1')
        namespaces = self.client.list_namespaces()
        self.assertEqual(2, len(namespaces))

    def test_workflow_operation(self):
        self.client.add_namespace('default')
        with Workflow(name='workflow1') as workflow:
            BashOperator(name='bash', bash_command='echo 1')
        workflow_meta = self.client.add_workflow(workflow.name, 'default', 'mock_content', pickle.dumps(workflow))
        self.assertEqual('workflow1', workflow_meta.name)
        self.assertEqual('default', workflow_meta.namespace)
        self.assertTrue(workflow_meta.is_enabled)
        self.assertEqual(-1, workflow_meta.event_offset)
        self.assertEqual(pickle.dumps(workflow), workflow_meta.workflow_object)

        workflow_meta = self.client.get_workflow(workflow.name, 'default')
        self.assertEqual('workflow1', workflow_meta.name)
        self.assertEqual('default', workflow_meta.namespace)
        self.assertTrue(workflow_meta.is_enabled)
        self.assertEqual(-1, workflow_meta.event_offset)
        self.assertEqual(pickle.dumps(workflow), workflow_meta.workflow_object)

        workflow_meta = self.client.update_workflow(workflow.name, 'default', 'new_content',
                                                    pickle.dumps(workflow), False)
        self.assertFalse(workflow_meta.is_enabled)

        self.client.enable_workflow(workflow.name, 'default')
        workflow_meta = self.client.get_workflow(workflow.name, 'default')
        self.assertTrue(workflow_meta.is_enabled)
        self.client.disable_workflow(workflow.name, 'default')
        workflow_meta = self.client.get_workflow(workflow.name, 'default')
        self.assertFalse(workflow_meta.is_enabled)

        self.client.add_workflow('workflow2', 'default', 'mock_content', pickle.dumps(workflow))
        self.client.add_workflow('workflow3', 'default', 'mock_content', pickle.dumps(workflow))
        workflows = self.client.list_workflows('default')
        self.assertEqual(3, len(workflows))

        workflows = self.client.list_workflows('default', page_size=2, offset=1)
        self.assertEqual(2, len(workflows))
        self.assertEqual('workflow2', workflows[0].name)
        self.assertEqual('workflow3', workflows[1].name)
        self.assertIsNone(self.client.list_workflows('non-exists-namespace'))

        self.assertTrue(self.client.delete_workflow(name='workflow2', namespace='default'))
        workflows = self.client.list_workflows('default')
        self.assertEqual(2, len(workflows))
        self.assertFalse(self.client.delete_workflow(name='non-exists', namespace='default'))

    @mock.patch('ai_flow.scheduler.rule_extractor.RuleExtractor.update_workflow')
    def test_workflow_snapshot_operation(self, mock_update):
        self.client.add_namespace('default')
        workflow_meta = self.client.add_workflow('workflow1', 'default', 'mock_content', b'111')
        snapshot1 = self.client.add_workflow_snapshot(workflow_meta.id, 'uri', b'111', 'md5')
        mock_update.assert_called_once_with(workflow_meta.id, b'111')

        got = self.client.get_workflow_snapshot(snapshot1.id)
        self.assertEqual('md5', got.signature)
        self.assertEqual(b'111', got.workflow_object)

        snapshot2 = self.client.add_workflow_snapshot(workflow_meta.id, 'uri', b'111', 'md5')
        snapshot3 = self.client.add_workflow_snapshot(workflow_meta.id, 'new_uri', b'111', 'new_md5')
        snapshots = self.client.list_workflow_snapshots(workflow_meta.id)
        self.assertEqual(3, len(snapshots))
        snapshots = self.client.list_workflow_snapshots(workflow_meta.id, page_size=1, offset=2)
        self.assertEqual(1, len(snapshots))
        self.assertEqual('new_uri', snapshots[0].uri)

        self.assertTrue(self.client.delete_workflow_snapshot(snapshot2.id))
        self.assertEqual(2, len(self.client.list_workflow_snapshots(workflow_meta.id)))
        self.assertFalse(self.client.delete_workflow_snapshot(10000))





