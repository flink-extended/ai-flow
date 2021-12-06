#!/usr/bin/env python
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
import argparse
import logging
import os
import signal

import ai_flow
from ai_flow.util.config_utils import create_default_server_config


def start_master(config_file):
    global server_runner
    server_runner = ai_flow.AIFlowServerRunner(config_file=config_file)
    server_runner.start(is_block=True)


def stop_master(signum, frame):
    global server_runner
    if server_runner:
        server_runner.stop()


def _prepare_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--generate-config-only', default=None, action='store_true',
                        help='Only generate notification server configuration file.')
    return parser.parse_args()


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, stop_master)
    server_runner = None
    if "AIFLOW_HOME" not in os.environ:
        os.environ["AIFLOW_HOME"] = os.environ["HOME"] + "/aiflow"
        logging.info("Set env variable AIFLOW_HOME to {}".format(os.environ["AIFLOW_HOME"]))
    logging.info("Looking for aiflow_server.yaml at {}".format(os.environ["AIFLOW_HOME"]))
    aiflow_server_config = os.environ["AIFLOW_HOME"] + "/aiflow_server.yaml"

    args = _prepare_args()

    if not os.path.exists(aiflow_server_config):
        create_default_server_config(os.environ.get("AIFLOW_HOME"))
        logging.info('AIFlow server config generated at {}.'.format(aiflow_server_config))
    else:
        logging.info("AIFlow server config exists at {}".format(aiflow_server_config))

    if args.generate_config_only:
        exit(0)

    start_master(aiflow_server_config)
