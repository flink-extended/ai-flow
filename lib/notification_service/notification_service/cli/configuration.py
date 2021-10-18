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
import os
from notification_service.server_config import NotificationServerConfig


def get_configuration():
    if 'NOTIFICATION_HOME' in os.environ:
        home = os.getenv('NOTIFICATION_HOME')
    else:
        home = os.getenv('HOME') + '/notification_service'
    config_file = home + '/notification_server.yaml'
    if not os.path.exists(config_file):
        raise FileNotFoundError('Do not find config file {}'.format(config_file))
    return NotificationServerConfig(config_file=config_file)
