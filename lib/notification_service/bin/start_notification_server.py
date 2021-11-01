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
import os
import logging
from typing import Dict
from notification_service.util import db
from notification_service.server_config import NotificationServerConfig
from notification_service.server import NotificationServerRunner


def create_server_config(root_dir_path, param: Dict[str, str]):
    """
    Generate default server config which use Apache Airflow as scheduler.
    """
    import notification_service.config_templates
    default_config_file_name = 'default_notification_server.yaml'
    config_file_name = 'notification_server.yaml'

    if not os.path.exists(root_dir_path):
        logging.info("{} does not exist, creating the directory".format(root_dir_path))
        os.makedirs(root_dir_path, exist_ok=False)
    default_server_config_path = os.path.join(
        os.path.dirname(notification_service.config_templates.__file__), default_config_file_name
    )
    if not os.path.exists(default_server_config_path):
        raise Exception("default notification server config is not found at {}.".format(default_server_config_path))

    server_config_target_path = os.path.join(root_dir_path, config_file_name)
    with open(default_server_config_path, encoding='utf-8') as config_file:
        default_config = config_file.read().format(**param)
    with open(server_config_target_path, mode='w', encoding='utf-8') as f:
        f.write(default_config)
    logging.info("Notification server config generated at {}".format(server_config_target_path))
    return server_config_target_path


def create_all_tables(db_uri):
    db.create_all_tables(db_uri)


def drop_all_tables(db_uri):
    db.drop_all_tables(db_uri)


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
    else:
        logging.info("Notification server config exists at {}".format(config_file))

    if args.generate_config_only:
        exit(0)

    config = NotificationServerConfig(config_file)
    create_all_tables(db_uri=config.db_uri)
    ns = NotificationServerRunner(config_file=config_file)
    logging.info('notification server start(port:{}).'.format(ns.config.port))
    ns.start(is_block=True)
