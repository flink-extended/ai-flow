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
from notification_service.client.embedded_notification_client import EmbeddedNotificationClient
from notification_service.model.event import DEFAULT_NAMESPACE

from ai_flow.rpc.client.scheduler_client import SchedulerClient

from ai_flow.common.configuration import config_constants


def get_scheduler_client(server_uri: str = None):
    """
    Create a client to connect with AIFlow scheduler server.

    :param server_uri: The uri of AIFlow server.
                       Use the default value in aiflow_client.yaml if not set.
    """
    if server_uri is None:
        server_uri = config_constants.SERVER_ADDRESS
    return SchedulerClient(server_uri=server_uri)


def get_notification_client(notification_server_uri: str = None,
                            namespace: str = None,
                            sender: str = None):
    """
    Create a notification client to connect with notification server.

    :param notification_server_uri: The uri of notification server.
    :param namespace: The event namespace.
    :param sender: The event sender.
    """
    if notification_server_uri is None:
        notification_server_uri = config_constants.NOTIFICATION_SERVER_URI
    return EmbeddedNotificationClient(
        server_uri=notification_server_uri,
        namespace=namespace,
        sender=sender)
