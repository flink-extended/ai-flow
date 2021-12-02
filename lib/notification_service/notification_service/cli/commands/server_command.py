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
import datetime
import logging
import os
import signal

import daemon
from daemon.pidfile import TimeoutPIDLockFile

import notification_service.settings
from notification_service.server import NotificationServerRunner
from notification_service.settings import get_configuration_file_path

logger = logging.getLogger(__name__)


def sigterm_handler(signum, frame):
    # We raise KeyboardInterrupt so that the server can stop gracefully
    raise KeyboardInterrupt()


def make_log_dir_if_not_exist():
    log_dir = os.path.join(notification_service.settings.NOTIFICATION_HOME, "logs")
    if os.path.exists(log_dir):
        return

    os.mkdir(log_dir)


def server_start(args):
    if args.daemon:
        make_log_dir_if_not_exist()
        log_path = os.path.join(notification_service.settings.NOTIFICATION_HOME, "logs",
                                'notification_server-{}.log'.format(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
        logger.info("Starting notification server in daemon pid: {}".format(os.getpid()))
        pid_file_path = os.path.join(notification_service.settings.NOTIFICATION_HOME, 'notification_server.pid')

        log = open(log_path, 'w+')
        ctx = _get_daemon_context(log, pid_file_path)

        with ctx:
            config_file_path = get_configuration_file_path()
            server_runner = NotificationServerRunner(config_file_path)
            server_runner.start(True)

        log.close()
    else:
        """Start the notification server"""
        signal.signal(signal.SIGTERM, sigterm_handler)
        config_file_path = get_configuration_file_path()
        server_runner = NotificationServerRunner(config_file_path)
        server_runner.start(True)


def _get_daemon_context(log, pid_file_path: str) -> daemon.DaemonContext:
    return daemon.DaemonContext(
        pidfile=TimeoutPIDLockFile(pid_file_path, -1),
        stdout=log,
        stderr=log,
    )
