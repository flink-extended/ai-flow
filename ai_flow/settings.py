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
import logging.config
import os

from ai_flow.common.env import get_aiflow_home


AIFLOW_HOME = get_aiflow_home()
AIFLOW_PID_FILENAME = 'aiflow_server.pid'
AIFLOW_WEBSERVER_PID_FILENAME = "aiflow_web_server.pid"

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
        },
        'task': {
            'class': 'ai_flow.common.util.log_util.file_task_handler.FileTaskHandler',
            'formatter': 'default',
            'base_log_folder': os.path.join(AIFLOW_HOME, 'logs'),
            'filename_template': '{{ workflow_name }}/{{ execution_id }}/{{ task_name }}/{{ seq_number }}.log',
        },
    },
    'loggers': {
        'aiflow.task': {
            'handlers': ['task'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
})
