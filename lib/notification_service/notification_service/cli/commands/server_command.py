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
"""Server command"""
import logging.config
import signal

from notification_service.server import NotificationServerRunner

from notification_service.settings import get_configuration_file_path


def sigterm_handler(signum, frame):
    # We raise KeyboardInterrupt so that the server can stop gracefully
    raise KeyboardInterrupt()


def server(args):
    """Start the notification server"""
    signal.signal(signal.SIGTERM, sigterm_handler)
    config_file_path = get_configuration_file_path()
    server_runner = NotificationServerRunner(config_file_path)
    server_runner.start(True)
