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
import unittest
from typing import Text
from ai_flow.plugin_interface.blob_manager_interface import BlobConfig, BlobManagerFactory, BlobManager


class MockBlockManager(BlobManager):
    def __init__(self, config):
        super().__init__(config)

    def upload(self, local_file_path: Text) -> Text:
        return 'upload'

    def download(self, remote_file_path: Text, local_dir: Text) -> Text:
        return 'download'


class TestBlobManager(unittest.TestCase):

    def test_blob_manager_factory(self):
        config = {
            'blob_manager_class': 'ai_flow.test.plugin_interface.test_blob_manager.MockBlockManager',
            'blob_manager_config': {
                'root_directory': '/tmp'
            }
        }
        blob_config = BlobConfig(config)
        blob_manager = BlobManagerFactory.create_blob_manager(blob_config.blob_manager_class(),
                                                              blob_config.blob_manager_config())
        uploaded_path = blob_manager.upload('')
        self.assertEqual('upload', uploaded_path)

        downloaded_path = blob_manager.download('', '')
        self.assertEqual('download', downloaded_path)


if __name__ == '__main__':
    unittest.main()
