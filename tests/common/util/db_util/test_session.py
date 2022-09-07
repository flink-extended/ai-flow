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
import unittest
from tempfile import TemporaryDirectory

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from ai_flow.common.configuration.config_constants import METADATA_BACKEND_URI
from ai_flow.common.util.db_util.session import create_session, create_sqlalchemy_engine, provide_session, \
    prepare_session, clear_engine_and_session

TestBase = declarative_base()


class TestTable(TestBase):
    __tablename__ = "test_table"

    id = Column(Integer, primary_key=True)
    name = Column(String(), nullable=False)

    def __init__(self, name, ):
        self.name = name


class TestSession(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        clear_engine_and_session()

    def test_create_session(self):
        with TemporaryDirectory(prefix='test_config') as tmp_dir:
            db_uri = "sqlite:///{}/aiflow.db".format(tmp_dir)
            prepare_session(db_uri=db_uri)
            TestBase.metadata.create_all(create_sqlalchemy_engine(db_uri))

            with create_session() as session:
                session.add(TestTable("name1"))
            with create_session() as session:
                self.assertEqual(1, len(session.query(TestTable).all()))

    def test_providered_session(self):
        @provide_session
        def session_op(session):
            session
            self.assertIsNotNone(session)
            self.assertEqual(str(session.bind.url), METADATA_BACKEND_URI)
        session_op()
