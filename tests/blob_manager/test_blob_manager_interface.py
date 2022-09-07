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

from ai_flow.blob_manager.blob_manager_interface import BlobManager, BlobManagerFactory, BlobManagerConfig


class MockBlockManager(BlobManager):
    def __init__(self, config):
        super().__init__(config)

    def upload(self, local_file_path: str) -> str:
        return 'upload'

    def download(self, remote_file_path: str, local_dir: str) -> str:
        return 'download'


class TestBlobManager(unittest.TestCase):

    def test_blob_manager_factory(self):
        config = {
            'blob_manager_class': 'tests.blob_manager.test_blob_manager_interface.MockBlockManager',
            'blob_manager_config': {
                'root_directory': '/tmp/ai-flow'
            }
        }
        blob_manager = BlobManagerFactory.create_blob_manager(BlobManagerConfig(config))
        uploaded_path = blob_manager.upload('')
        self.assertEqual('upload', uploaded_path)

        downloaded_path = blob_manager.download('', '')
        self.assertEqual('download', downloaded_path)

    def test_config(self):
        config = BlobManagerConfig({
            'blob_manager_class': 'ai_flow.blob_manager.impl.local_blob_manager.LocalBlobManager',
            'blob_manager_config': {
                'root_directory': '/tmp/ai-flow'
            }
        })
        self.assertEqual('ai_flow.blob_manager.impl.local_blob_manager.LocalBlobManager', config.get_class())
        self.assertEqual({'root_directory': '/tmp/ai-flow'}, config.get_customized_config())


if __name__ == '__main__':
    unittest.main()
