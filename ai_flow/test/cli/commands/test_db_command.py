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
import ai_flow.settings

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from ai_flow.cli import cli_parser
from ai_flow.cli.commands import db_command
from ai_flow.settings import get_configuration
from ai_flow.store.db.db_model import SqlProject


class TestCliDb(unittest.TestCase):
    prev_aiflow_home = None

    @classmethod
    def setUpClass(cls):
        cls.parser = cli_parser.get_parser()
        cls.prev_aiflow_home = ai_flow.settings.AIFLOW_HOME
        ai_flow.settings.AIFLOW_HOME = os.path.join(os.path.dirname(__file__), '../')
        cls.config = get_configuration()

    @classmethod
    def tearDownClass(cls) -> None:
        ai_flow.settings.AIFLOW_HOME = cls.prev_aiflow_home

    def _remove_db_file(self):
        if os.path.exists('aiflow.db'):
            os.remove('aiflow.db')

    def setUp(self) -> None:
        self._remove_db_file()

    def tearDown(self) -> None:
        self._remove_db_file()

    def test_cli_db_init(self):
        db_command.init(self.parser.parse_args(['db', 'init']))
        engine = create_engine(self.config.get_db_uri())
        self.assertTrue('project' in engine.table_names())
        self.assertTrue('aiflow_member' in engine.table_names())

    def test_cli_db_reset(self):
        db_command.init(self.parser.parse_args(['db', 'init']))
        engine = create_engine(self.config.get_db_uri())
        Session = scoped_session(
            sessionmaker(autocommit=False,
                         autoflush=False,
                         bind=engine,
                         expire_on_commit=False))
        session = Session()
        project = SqlProject()
        project.name = 'a'
        project.uri = 'a'
        session.add(project)
        session.commit()
        project_result = session.query(SqlProject).all()
        self.assertEqual(1, len(project_result))
        db_command.reset(self.parser.parse_args(['db', 'reset', '-y']))
        project_result = session.query(SqlProject).all()
        self.assertEqual(0, len(project_result))
        session.close()

    def test_cli_db_upgrade(self):
        db_command.upgrade(self.parser.parse_args(['db', 'upgrade', '--version', 'de1c96ef582a']))
        engine = create_engine(self.config.get_db_uri())
        self.assertTrue('project' in engine.table_names())
        self.assertFalse('aiflow_member' in engine.table_names())

    def test_cli_db_downgrade(self):
        db_command.init(self.parser.parse_args(['db', 'init']))
        db_command.downgrade(self.parser.parse_args(['db', 'downgrade', '--version', 'de1c96ef582a']))
        engine = create_engine(self.config.get_db_uri())
        self.assertTrue('project' in engine.table_names())
        self.assertFalse('aiflow_member' in engine.table_names())


if __name__ == '__main__':
    unittest.main()
