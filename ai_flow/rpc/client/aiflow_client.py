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
from notification_service.embedded_notification_client import EmbeddedNotificationClient
from notification_service.event import DEFAULT_NAMESPACE

from ai_flow.rpc.client.scheduler_client import SchedulerClient

from ai_flow.common.configuration import config_constants


def get_scheduler_client():
    server_uri = config_constants.SERVER_ADDRESS
    return SchedulerClient(server_uri=server_uri)


def get_notification_client(namespace=DEFAULT_NAMESPACE, sender=None):
    return EmbeddedNotificationClient(
        server_uri=config_constants.NOTIFICATION_SERVER_URI,
        namespace=namespace,
        sender=sender)
