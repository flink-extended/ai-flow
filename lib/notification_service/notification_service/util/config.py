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
"""Utilities module for config"""
import logging
import os

from typing import Dict

logger = logging.getLogger(__name__)


def create_server_config(root_dir_path, param: Dict[str, str]):
    """
    Generate the default config of the Notification Server.
    """
    import notification_service.config_templates
    default_config_file_name = 'default_notification_server.yaml'
    config_file_name = 'notification_server.yaml'

    if not os.path.exists(root_dir_path):
        logging.info('{} does not exist, creating the directory.'.format(root_dir_path))
        os.makedirs(root_dir_path, exist_ok=False)
    default_server_config_path = os.path.join(
        os.path.dirname(notification_service.config_templates.__file__), default_config_file_name
    )
    if not os.path.exists(default_server_config_path):
        raise Exception('Default notification server config is not found at {}.'.format(default_server_config_path))

    server_config_target_path = os.path.join(root_dir_path, config_file_name)
    with open(default_server_config_path, encoding='utf-8') as config_file:
        default_config = config_file.read().format(**param)
    with open(server_config_target_path, mode='w', encoding='utf-8') as f:
        f.write(default_config)
    return server_config_target_path
