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
import os

from ai_flow.endpoint.server.server_config import AIFlowServerConfig


def get_aiflow_home():
    if 'AIFLOW_HOME' in os.environ:
        home = os.getenv('AIFLOW_HOME')
    else:
        home = os.getenv('HOME') + '/aiflow'
    return home


AIFLOW_HOME = get_aiflow_home()


def get_configuration_file_path():
    config_file_path = AIFLOW_HOME + '/aiflow_server.yaml'
    if not os.path.exists(config_file_path):
        raise FileNotFoundError('Config file {} not found.'.format(config_file_path))
    return config_file_path


def get_configuration():
    config_file_path = get_configuration_file_path()
    config = AIFlowServerConfig()
    config.load_from_file(config_file_path)
    return config
