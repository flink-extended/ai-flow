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
import logging.config
import os

from notification_service.util.server_config import NotificationServerConfig

# We hard code the logging config, we should make it configurable in the future.
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[%(asctime)s - %(filename)s:%(lineno)d [%(threadName)s] - %(levelname)s: %(message)s',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stderr',
            'formatter': 'default'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
})


def get_notification_home():
    if 'NOTIFICATION_HOME' in os.environ:
        home = os.getenv('NOTIFICATION_HOME')
    else:
        home = os.getenv('HOME') + '/notification_service'
    return home


NOTIFICATION_HOME = get_notification_home()
NOTIFICATION_PID_FILENAME = 'notification_server.pid'


def get_configuration_file_path(notification_home=None):
    if not notification_home:
        notification_home = NOTIFICATION_HOME
    config_file_path = notification_home + '/notification_server.yaml'
    if not os.path.exists(config_file_path):
        raise FileNotFoundError('Do not find config file {}'.format(config_file_path))
    return config_file_path


def get_configuration():
    config_file_path = get_configuration_file_path()
    return NotificationServerConfig(config_file=config_file_path)
