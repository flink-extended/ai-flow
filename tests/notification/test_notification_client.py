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
import json
import unittest
from unittest import mock

from notification_service.model.event import Event, EventKey

from ai_flow.model.internal.contexts import set_runtime_task_context, TaskExecutionContext
from ai_flow.model.internal.events import EventContextConstant
from ai_flow.model.task_execution import TaskExecutionKey
from ai_flow.notification.notification_client import AIFlowNotificationClient
from tests.test_utils.mock_utils import MockNotificationClient


class TestNotificationClient(unittest.TestCase):

    def setUp(self) -> None:
        task_execution_key = TaskExecutionKey(1, "task_1", 1)
        set_runtime_task_context(TaskExecutionContext(task_execution_key))

    def test_send_event(self):
        with mock.patch('ai_flow.notification.notification_client.EmbeddedNotificationClient', MockNotificationClient):
            client = AIFlowNotificationClient(
                server_uri="localhost:8888",
            )
            event = Event(EventKey(event_name="event_name"), message="message")
            actual_sent_event = client.send_event(event)
            self.assertEqual(json.dumps({
                EventContextConstant.WORKFLOW_EXECUTION_ID: 1
            }), actual_sent_event.context)
            self.assertEqual("message", actual_sent_event.message)
