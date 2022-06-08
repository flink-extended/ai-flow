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
import unittest

from ai_flow.common.util.db_util.db_migration import init_db
from ai_flow.common.util.db_util.session import new_session
from ai_flow.metadata.metadata_manager import MetadataManager


class BaseUnitTest(unittest.TestCase):
    def setUp(self) -> None:
        self.file = 'test.db'
        self._delete_db_file()
        self.url = 'sqlite:///{}'.format(self.file)
        init_db(self.url)
        self.session = new_session(db_uri=self.url)

    def _delete_db_file(self):
        if os.path.exists(self.file):
            os.remove(self.file)

    def tearDown(self) -> None:
        self.session.close()
        self._delete_db_file()


class UnitTestWithMetadataManager(BaseUnitTest):
    def setUp(self) -> None:
        super().setUp()
        self.metadata_manager = MetadataManager(session=self.session)


class UnitTestWithNamespace(UnitTestWithMetadataManager):
    def setUp(self) -> None:
        super().setUp()
        self.namespace_name = 'namespace'
        self.namespace_meta = self.metadata_manager.add_namespace(name=self.namespace_name, properties={'a': 'a'})
        self.metadata_manager.flush()
