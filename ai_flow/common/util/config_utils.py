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

logger = logging.getLogger(__name__)


def create_default_server_config(root_dir_path):
    """
    Generate the default config of the AIFlow Server.
    """
    import ai_flow.config_templates
    if not os.path.exists(root_dir_path):
        logging.info("{} does not exist, creating the directory".format(root_dir_path))
        os.makedirs(root_dir_path, exist_ok=False)
    aiflow_server_config_path = os.path.join(
        os.path.dirname(ai_flow.config_templates.__file__), "default_aiflow_server.yaml"
    )
    if not os.path.exists(aiflow_server_config_path):
        raise Exception("Default aiflow server config is not found at {}.".format(aiflow_server_config_path))

    aiflow_server_config_target_path = os.path.join(root_dir_path, "aiflow_server.yaml")
    with open(aiflow_server_config_path, encoding='utf-8') as config_file:
        default_config = config_file.read().format(**{'AIFLOW_HOME': root_dir_path})
    with open(aiflow_server_config_target_path, mode='w', encoding='utf-8') as f:
        f.write(default_config)
    return aiflow_server_config_target_path
