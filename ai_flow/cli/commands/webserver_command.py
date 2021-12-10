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

import daemon
from daemon.pidfile import TimeoutPIDLockFile

import ai_flow.settings
from ai_flow.frontend.web_server import start_web_server_by_config_file_path
from ai_flow.settings import get_configuration_file_path
from ai_flow.util.process_utils import check_pid_exist, stop_process

logger = logging.getLogger(__name__)


def make_log_dir_if_not_exist():
    log_dir = os.path.join(ai_flow.settings.AIFLOW_HOME, "logs")
    if os.path.exists(log_dir):
        return

    os.makedirs(log_dir, exist_ok=True)


def webserver_start(args):
    pid_file_path = os.path.join(ai_flow.settings.AIFLOW_HOME, ai_flow.settings.AIFLOW_WEBSERVER_PID_FILENAME)
    if os.path.exists(pid_file_path):
        with open(pid_file_path, 'r') as f:
            pid = int(f.read())
        if not check_pid_exist(pid):
            logger.info(
                "Process pid: {} does not exist. This means a staled PID file. Removing the PID file".format(pid))
            os.remove(pid_file_path)
        else:
            logger.info("Web Server is running, stop it first with 'aiflow webserver stop'.")
            return
    if args.daemon:
        make_log_dir_if_not_exist()
        log_path = os.path.join(ai_flow.settings.AIFLOW_HOME, "logs",
                                'aiflow_web_server-{}.log'.format(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
        logger.info(f"\nStarting AIFlow Webserver in daemon mode\n"
                    f"AIFlow Webserver log: {log_path}\n"
                    f"AIFlow Webserver pid file: {pid_file_path}")

        log = open(log_path, 'w+')
        ctx = daemon.DaemonContext(
            pidfile=TimeoutPIDLockFile(pid_file_path, -1),
            stdout=log,
            stderr=log
        )
        with ctx:
            config_file_path = get_configuration_file_path()
            start_web_server_by_config_file_path(config_file_path)

        log.close()
    else:
        """Starts the AIFlow Webserver"""
        config_file_path = get_configuration_file_path()

        pid = os.getpid()
        logger.info("Starting AIFlow Webserver at pid: {}".format(pid))
        with open(pid_file_path, 'w') as f:
            f.write(str(pid))
        try:
            start_web_server_by_config_file_path(config_file_path)
        finally:
            if os.path.exists(pid_file_path):
                os.remove(pid_file_path)


def webserver_stop(args):
    pid_file_path = os.path.join(ai_flow.settings.AIFLOW_HOME,
                                 ai_flow.settings.AIFLOW_WEBSERVER_PID_FILENAME)
    if not os.path.exists(pid_file_path):
        logger.info(
            "PID file of AIFlow Webserver does not exist at {}. The AIFlow Webserver is not running.".format(
                pid_file_path))
        return

    with open(pid_file_path, 'r') as f:
        pid = int(f.read())

    if not check_pid_exist(pid):
        logger.info("Process pid: {} does not exist. This means a staled PID file. Removing the PID file".format(pid))
        os.remove(pid_file_path)
        return

    stop_process(pid, "AIFlow Webserver")
