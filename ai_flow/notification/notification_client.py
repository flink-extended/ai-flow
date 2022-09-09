#
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
import json
from datetime import datetime
from typing import List, Optional

from notification_service.client.embedded_notification_client import EmbeddedNotificationClient

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.model.internal.contexts import get_runtime_task_context
from ai_flow.model.internal.events import EventContextConstant

import notification_service.model.event as notification_event
import notification_service.client.notification_client as notification_client

Event = notification_event.Event
ListenerProcessor = notification_client.ListenerProcessor
ListenerRegistrationId = notification_client.ListenerRegistrationId


class AIFlowNotificationClient(object):

    def __init__(self, server_uri: str):
        self.context = get_runtime_task_context()
        if not self.context:
            raise AIFlowException("AIFlowNotificationClient can only be used in AIFlow operators.")
        self.client = EmbeddedNotificationClient(
            server_uri=server_uri,
            namespace=self.context.workflow.namespace,
            sender=str(self.context.task_execution_key)
        )

    def send_event(self, key: str, value: Optional[str] = None):
        """
        Send event to current workflow execution. This function can only be used
        in AIFlow Operator runtime. It will retrieve the workflow execution info from runtime
        context and set to context of the event.

        :param key: the key of the event.
        :param value: optional, the value of the event.
        """
        workflow_execution_id = self.context.task_execution_key.workflow_execution_id
        event = Event(key=key, value=value)
        event.context = json.dumps({
            EventContextConstant.WORKFLOW_EXECUTION_ID: workflow_execution_id
        })
        return self.client.send_event(event)

    def register_listener(self,
                          listener_processor: ListenerProcessor,
                          event_keys: List[str] = None,
                          begin_time: datetime = None) -> ListenerRegistrationId:
        begin_time = begin_time or datetime.now()
        offset = self.client.time_to_offset(begin_time)
        return self.client.register_listener(
            listener_processor=listener_processor,
            event_keys=event_keys,
            offset=offset
        )

    def unregister_listener(self, registration_id: ListenerRegistrationId):
        self.client.unregister_listener(registration_id)

    def close(self):
        self.client.close()
