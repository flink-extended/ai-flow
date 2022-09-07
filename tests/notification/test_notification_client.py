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
import json
import unittest
from unittest import mock

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.model.internal.contexts import set_runtime_task_context, TaskExecutionContext
from ai_flow.model.internal.events import EventContextConstant
from ai_flow.model.task_execution import TaskExecutionKey
from ai_flow.model.workflow import Workflow
from ai_flow.notification.notification_client import AIFlowNotificationClient
from tests.test_utils.mock_utils import MockNotificationClient


class TestNotificationClient(unittest.TestCase):

    def setUp(self) -> None:
        workflow = Workflow(name='workflow', namespace='namespace')
        task_execution_key = TaskExecutionKey(1, "task_1", 1)
        set_runtime_task_context(TaskExecutionContext(workflow, task_execution_key))

    def test_create_client_without_context(self):
        set_runtime_task_context(None)
        with self.assertRaisesRegex(AIFlowException, r"can only be used in AIFlow operators"):
            AIFlowNotificationClient(server_uri="localhost:8888")

    def test_send_event(self):
        with mock.patch('ai_flow.notification.notification_client.EmbeddedNotificationClient', MockNotificationClient):
            client = AIFlowNotificationClient(
                server_uri="localhost:8888",
            )
            actual_sent_event = client.send_event(key="event_name", value="message")
            self.assertEqual(json.dumps({
                EventContextConstant.WORKFLOW_EXECUTION_ID: 1
            }), actual_sent_event.context)
            self.assertEqual("event_name", actual_sent_event.key)
            self.assertEqual("message", actual_sent_event.value)
            self.assertEqual("namespace", actual_sent_event.namespace)
            self.assertEqual("1_task_1_1", actual_sent_event.sender)
