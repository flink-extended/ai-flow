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
import os
import unittest

from sqlalchemy import create_engine

from notification_service.cli import cli_parser
from notification_service.cli.commands import db_command
from notification_service.server_config import get_configuration
from notification_service.util import db


class TestCliDb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = cli_parser.get_parser()
        os.environ['NOTIFICATION_HOME'] = os.path.join(os.path.dirname(__file__), '../../')
        cls.config = get_configuration()

    def _remove_db_file(self):
        if os.path.exists('ns.db'):
            os.remove('ns.db')

    def setUp(self) -> None:
        self._remove_db_file()
        db.SQL_ALCHEMY_CONN = self.config.db_uri

    def tearDown(self) -> None:
        self._remove_db_file()
        db.clear_engine_and_session()

    def test_cli_db_init(self):
        db_command.init(self.parser.parse_args(['db', 'init']))
        engine = create_engine(self.config.db_uri)
        self.assertTrue('event_model' in engine.table_names())
        self.assertTrue('member_model' in engine.table_names())
        self.assertTrue('notification_client' in engine.table_names())

    def test_cli_db_reset(self):
        db_command.init(self.parser.parse_args(['db', 'init']))
        db.prepare_db()
        with db.create_session() as session:
            client = db.ClientModel()
            client.namespace = 'a'
            client.sender = 'a'
            client.create_time = 1
            session.add(client)
            session.commit()
            client_res = session.query(db.ClientModel).all()
            self.assertEqual(1, len(client_res))
            db_command.reset(self.parser.parse_args(['db', 'reset', '-y']))
            client_res = session.query(db.ClientModel).all()
            self.assertEqual(0, len(client_res))

    def test_cli_db_upgrade(self):
        db_command.upgrade(self.parser.parse_args(['db', 'upgrade', '--version', '87cb292bcc31']))
        engine = create_engine(self.config.db_uri)
        self.assertTrue('event_model' in engine.table_names())
        self.assertTrue('notification_client' in engine.table_names())
        self.assertFalse('member_model' in engine.table_names())

    def test_cli_db_downgrade(self):
        db_command.init(self.parser.parse_args(['db', 'init']))
        db_command.downgrade(self.parser.parse_args(['db', 'downgrade', '--version', '87cb292bcc31']))
        engine = create_engine(self.config.db_uri)
        self.assertTrue('event_model' in engine.table_names())
        self.assertTrue('notification_client' in engine.table_names())
        self.assertFalse('member_model' in engine.table_names())


if __name__ == '__main__':
    unittest.main()
