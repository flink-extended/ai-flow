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
import os
from notification_service.server import NotificationServerRunner
from notification_service.util import db

_NS_DB_FILE = 'ns.db'
_NS_DB_URI = '%s%s' % ('sqlite:///', _NS_DB_FILE)
_NS_PORT = '50052'
_NS_URI = 'localhost:%s' % _NS_PORT


def start_notification_server():
    if os.path.exists(_NS_DB_FILE):
        os.remove(_NS_DB_FILE)
    config_file = os.path.dirname(os.path.dirname(__file__)) + '/notification_server.yaml'
    ns_server = NotificationServerRunner(config_file=config_file)
    db.create_all_tables(ns_server.config.db_uri)
    ns_server.start()
    return ns_server


def stop_notification_server(ns_server):
    ns_server.stop()
    os.remove(_NS_DB_FILE)
