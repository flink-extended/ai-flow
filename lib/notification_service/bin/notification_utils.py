#!/usr/bin/env python
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
import argparse
import os
import logging
from typing import Dict
from notification_service.util import db
from notification_service.server_config import NotificationServerConfig


def create_sever_config(root_dir_path, param: Dict[str, str]):
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
    return server_config_target_path


def create_all_tables(db_uri):
    db.create_all_tables(db_uri)


def drop_all_tables(db_uri):
    db.drop_all_tables(db_uri)


def _prepare_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gen-config', required=False, action='store_true',
                        help='Generate the notification server configuration file. '
                             'Usage:  --gen-config [configuration file dir]')
    parser.add_argument('--db', required=False, choices={'init', 'clean', 'reset'},
                        help='Usage: --db init [Create all tables of the notification server.] '
                             '--db clean [Drop all tables of the notification server.]')

    return parser.parse_args()


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s',
                        level=logging.INFO)
    args = _prepare_args()
    if args.db is not None:
        config = NotificationServerConfig(os.environ.get("NOTIFICATION_CONFIG_FILE"))
        if 'init' == args.db:
            create_all_tables(config.db_uri)
        elif 'clean' == args.db:
            drop_all_tables(config.db_uri)
        elif 'reset' == args.db:
            drop_all_tables(config.db_uri)
            create_all_tables(config.db_uri)
    elif args.gen_config is True:
        create_sever_config(os.environ.get("NOTIFICATION_HOME"), os.environ.copy())
    else:
        raise Exception("Must set -gen-config or --db")
