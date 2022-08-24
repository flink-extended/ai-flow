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
from unittest import mock

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.rpc.client.aiflow_client import get_scheduler_client
from ai_flow.rpc.server.server import AIFlowServer
from tests.test_utils.unittest_base import BaseUnitTest


class TestNamespaceRpc(BaseUnitTest):
    def setUp(self) -> None:
        super().setUp()
        with mock.patch("ai_flow.task_executor.common.task_executor_base.HeartbeatManager"):
            with mock.patch('ai_flow.rpc.service.scheduler_service.get_notification_client'):
                with mock.patch('ai_flow.task_executor.common.task_executor_base.get_notification_client'):
                    self.server = AIFlowServer()
                    self.server.run(is_block=False)
        self.client = get_scheduler_client()

    def tearDown(self) -> None:
        self.server.stop()
        super().tearDown()

    def test_namespace_operation(self):
        self.client.delete_namespace('default')

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

        with self.assertRaisesRegex(AIFlowException, r"Namespace non-exists not exists"):
            self.assertFalse(self.client.delete_namespace('non-exists'))
        self.client.delete_namespace('ns1')
        namespaces = self.client.list_namespaces()
        self.assertEqual(2, len(namespaces))