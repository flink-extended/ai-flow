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

import io
import time
import unittest
from contextlib import redirect_stdout
from datetime import datetime

from notification_service.cli import cli_parser
from notification_service.cli.commands import event_command
from notification_service.client import NotificationClient
from notification_service.event_storage import MemoryEventStorage
from notification_service.server import NotificationServer
from notification_service.service import NotificationService
from notification_service.util import db

SERVER_URI = "localhost:50051"


class TestCliEvent(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.parser = cli_parser.get_parser()
        db.create_all_tables()
        cls.storage = MemoryEventStorage()
        cls.master = NotificationServer(NotificationService(cls.storage))
        cls.master.run()
        cls.wait_for_master_started(server_uri=SERVER_URI)

    @classmethod
    def tearDownClass(cls):
        cls.master.stop()
        cls.storage.clean_up()

    def setUp(self):
        self.storage.clean_up()

    def tearDown(self):
        self.storage.clean_up()

    @classmethod
    def wait_for_master_started(cls, server_uri):
        last_exception = None
        for i in range(60):
            try:
                return NotificationClient(server_uri=server_uri)
            except Exception as e:
                time.sleep(1)
                last_exception = e
        raise Exception("The server %s is unavailable." % server_uri) from last_exception

    def send_an_event(self, key='key'):
        event_command.send_event(
            self.parser.parse_args(
                ['event',
                 'send',
                 '-s', SERVER_URI,
                 '-k', key,
                 '-n', 'namespace1',
                 '-v', 'value1',
                 '--event-type', 'event-type1',
                 '--sender', 'sender1',
                 '--context', 'context1']
            )
        )

    def test_event_cli_invalid(self):
        with redirect_stdout(io.StringIO()) as stdout:
            event_command.send_event(
                self.parser.parse_args(
                    ['event',
                     'send',
                     '-k', 'key']
                )
            )
        self.assertIn('Argument --server-uri not set', stdout.getvalue())
        with redirect_stdout(io.StringIO()) as stdout:
            event_command.send_event(
                self.parser.parse_args(
                    ['event',
                     'send',
                     '-s', 'uri']
                )
            )
        self.assertIn('Argument --key not set', stdout.getvalue())

    def test_cli_send_events(self):
        with redirect_stdout(io.StringIO()) as stdout:
            event_command.send_event(
                self.parser.parse_args(
                    ['event',
                     'send',
                     '-s', SERVER_URI,
                     '-k', 'key',
                     ]
                )
            )
            self.send_an_event()
        self.assertIn('Arguments --value not set.', stdout.getvalue())
        self.assertIn('value1', stdout.getvalue())
        self.assertIn('event-type1', stdout.getvalue())
        self.assertIn('namespace1', stdout.getvalue())
        self.assertIn('context1', stdout.getvalue())
        self.assertIn('sender1', stdout.getvalue())

    def test_cli_list_events(self):
        self.send_an_event('key1')
        self.send_an_event('key2')
        with redirect_stdout(io.StringIO()) as stdout:
            event_command.list_events(
                self.parser.parse_args(
                    ['event',
                     'list',
                     '-s', SERVER_URI,
                     '-k', 'key1'
                     ]
                )
            )
        self.assertIn('key1', stdout.getvalue())
        self.assertNotIn('key2', stdout.getvalue())

        self.send_an_event('key1')
        self.send_an_event('key2')
        with redirect_stdout(io.StringIO()) as stdout:
            event_command.list_events(
                self.parser.parse_args(
                    ['event',
                     'list',
                     '-s', SERVER_URI,
                     '-k', 'key1',
                     '-n', 'invalid'
                     ]
                )
            )
        self.assertNotIn('key1', stdout.getvalue())

    def test_cli_count_events(self):
        self.send_an_event('key1')
        time.sleep(1)
        current_time = datetime.now().isoformat()
        self.send_an_event('key1')
        self.send_an_event('key2')
        with redirect_stdout(io.StringIO()) as stdout:
            event_command.count_events(
                self.parser.parse_args(
                    ['event',
                     'count',
                     '-s', SERVER_URI,
                     '-k', 'key1'
                     ]
                )
            )
        self.assertEquals('2\n', stdout.getvalue())

        with redirect_stdout(io.StringIO()) as stdout:
            event_command.count_events(
                self.parser.parse_args(
                    ['event',
                     'count',
                     '-s', SERVER_URI,
                     '-k', 'key1',
                     '--begin-version', '1'
                     ]
                )
            )
        self.assertEquals('1\n', stdout.getvalue())

        with redirect_stdout(io.StringIO()) as stdout:
            event_command.count_events(
                self.parser.parse_args(
                    ['event',
                     'count',
                     '-s', SERVER_URI,
                     '-k', 'key1',
                     '--begin-time', current_time
                     ]
                )
            )
        self.assertEquals('1\n', stdout.getvalue())

        with redirect_stdout(io.StringIO()) as stdout:
            event_command.count_events(
                self.parser.parse_args(
                    ['event',
                     'count',
                     '-s', SERVER_URI,
                     '-k', 'key1',
                     '--namespace', 'invalid'
                     ]
                )
            )
        self.assertEquals('0\n', stdout.getvalue())
