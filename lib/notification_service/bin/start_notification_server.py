#!/usr/bin/env python
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
import argparse
import logging
import os

from notification_service.server import NotificationServerRunner
from notification_service.server_config import NotificationServerConfig
from notification_service.util import db
from notification_service.util.server_config import create_server_config


def _prepare_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--generate-config-only', default=None, action='store_true',
                        help='Only generate notification server configuration file.')
    return parser.parse_args()


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s',
                        level=logging.INFO)
    if "NOTIFICATION_HOME" not in os.environ:
        os.environ["NOTIFICATION_HOME"] = os.environ["HOME"] + "/notification_service"
        logging.info("Set env variable NOTIFICATION_HOME to {}".format(os.environ["NOTIFICATION_HOME"]))
    if not os.path.exists(os.environ["NOTIFICATION_HOME"]):
        os.makedirs(os.environ["NOTIFICATION_HOME"])
    config_file = os.environ["NOTIFICATION_HOME"] + "/notification_server.yaml"

    args = _prepare_args()

    if not os.path.exists(config_file):
        create_server_config(os.environ.get("NOTIFICATION_HOME"), os.environ.copy())
        logging.info('Notification server config generated at {}.'.format(config_file))
    else:
        logging.info("Notification server config exists at {}".format(config_file))

    if args.generate_config_only:
        exit(0)

    config = NotificationServerConfig(config_file)
    db.create_all_tables(config.db_uri)
    ns = NotificationServerRunner(config_file=config_file)
    logging.info('notification server start(port:{}).'.format(ns.config.port))
    ns.start(is_block=True)
