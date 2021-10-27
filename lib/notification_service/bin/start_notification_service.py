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
from notification_service.master import NotificationServerRunner


def _prepare_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config-file', type=str, default=None,
                        help='The notification server configuration file.')
    return parser.parse_args()


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s',
                        level=logging.INFO)
    args = _prepare_args()
    config_file = args.config_file
    ns = NotificationServerRunner(config_file=config_file)
    logging.info('notification service start(port:{}).'.format(ns.config.port))
    ns.start(is_block=True)
