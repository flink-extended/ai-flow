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
import logging
import multiprocessing
import os
import signal
import time
import unittest

from notification_service.cli import cli_parser
from notification_service.cli.commands import server_command, db_command
from notification_service.client import NotificationClient

logger = logging.getLogger(__name__)


class TestCliServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = cli_parser.get_parser()

    def test_cli_server_start(self):
        os.environ["NOTIFICATION_HOME"] = os.path.join(os.path.dirname(__file__), "..", "..")
        db_command.upgrade(self.parser.parse_args(['db', 'upgrade']))
        server_process = multiprocessing.Process(target=server_command.server,
                                                 args=(self.parser.parse_args(['server']),), )
        server_process.start()
        time.sleep(1)

        client = NotificationClient(server_uri="localhost:50052")
        self.assertEqual(0, client.get_latest_version())

        os.kill(server_process.pid, signal.SIGTERM)

        server_process.join(None)

        os.remove("./ns.db")
