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
#
import json
from datetime import datetime
from typing import List

from notification_service.client.embedded_notification_client import EmbeddedNotificationClient
from notification_service.client.notification_client import ListenerRegistrationId, \
    ListenerProcessor
from notification_service.model.event import Event, EventKey

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.model.internal.contexts import get_runtime_task_context
from ai_flow.model.internal.events import EventContextConstant


class AIFlowNotificationClient(object):

    def __init__(self,
                 server_uri: str,
                 namespace: str = None,
                 sender: str = None,
                 client_id: int = None,
                 initial_seq_num: int = None):
        self.client = EmbeddedNotificationClient(
            server_uri=server_uri,
            namespace=namespace,
            sender=sender,
            client_id=client_id,
            initial_seq_num=initial_seq_num
        )

    def send_event_to_all_workflow_executions(self, event: Event) -> Event:
        """
        Send event to all workflow executions.

        :param event: the event to send.
        :return: The sent event.
        """
        return self.client.send_event(event)

    def send_event(self, event: Event) -> Event:
        """
        Send event to current workflow execution. This function can only be used
        in AIFlow Operator runtime. It will retrieve the workflow execution info from runtime
        context and set to context of the event.

        :param event: the event to send.
        :return: The sent event.
        """
        context = get_runtime_task_context()
        if not context:
            raise AIFlowException("send_event can only be used in AIFlow Operator runtime.")
        workflow_execution_id = context.task_execution_key.workflow_execution_id
        if event.context is not None:
            context_dict: dict = json.loads(event.context)
            context_dict.update({
                EventContextConstant.WORKFLOW_EXECUTION_ID: workflow_execution_id
            })
        else:
            event.context = json.dumps({
                EventContextConstant.WORKFLOW_EXECUTION_ID: workflow_execution_id
            })
        return self.client.send_event(event)

    def register_listener(self,
                          listener_processor: ListenerProcessor,
                          event_keys: List[EventKey] = None,
                          offset: int = None) -> ListenerRegistrationId:
        return self.client.register_listener(
            listener_processor=listener_processor,
            event_keys=event_keys,
            offset=offset
        )

    def unregister_listener(self, registration_id: ListenerRegistrationId):
        self.client.unregister_listener(registration_id)

    def list_events(self, name: str = None, namespace: str = None, event_type: str = None, sender: str = None,
                    offset: int = None) -> List[Event]:
        return self.client.list_events(
            name=name,
            namespace=namespace,
            event_type=event_type,
            sender=sender,
            offset=offset
        )

    def time_to_offset(self, time: datetime) -> int:
        return self.client.time_to_offset(time)
