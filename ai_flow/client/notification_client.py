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
from typing import Optional
import logging
from ai_flow.context.job_context import current_job_name
from ai_flow.context.project_context import current_project_config
from notification_service.client import NotificationClient

_default_notification_client_dict = {}


def get_notification_client() -> Optional[NotificationClient]:
    """Get the default notification client."""
    global _default_notification_client_dict
    current_uri = current_project_config().get_notification_server_uri()
    if current_uri is None:
        logging.warning("The project config do not set notification_server_uri item.")
        return None
    else:
        if current_job_name() in _default_notification_client_dict:
            return _default_notification_client_dict[current_job_name()]
        else:
            ha_flag = True if len(current_uri.split(',')) > 1 else False
            notification_client \
                = NotificationClient(server_uri=current_uri,
                                     enable_ha=ha_flag,
                                     default_namespace=current_project_config().get_project_name(),
                                     sender=current_job_name()
                                     )
            _default_notification_client_dict[current_job_name()] = notification_client
            return notification_client
