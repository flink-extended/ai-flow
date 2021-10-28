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
import shutil
import unittest
import os
from ai_flow.util.path_util import get_file_dir
from ai_flow.plugin_interface.blob_manager_interface import BlobManagerFactory, BlobConfig

_TMP_FOLDER = '/tmp/' + __name__
_TMP_FILE = os.path.join(_TMP_FOLDER, 'file.txt')


class TestHDFSBlobManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        os.mkdir(_TMP_FOLDER)

    @classmethod
    def tearDownClass(cls) -> None:
        if os.path.exists(_TMP_FOLDER):
            shutil.rmtree(_TMP_FOLDER)

    def setUp(self) -> None:
        file = open(_TMP_FILE, 'w')
        file.close()

    def tearDown(self) -> None:
        if os.path.exists(_TMP_FILE):
            os.remove(_TMP_FILE)

    @unittest.skipUnless((os.environ.get('blob_server.hdfs_url') is not None
                          and os.environ.get('blob_server.hdfs_user') is not None
                          and os.environ.get('blob_server.repo_name') is not None), 'need set hdfs config')
    def test_project_upload_download_hdfs(self):
        config = {
            'blob_manager_class': 'ai_flow_plugins.blob_manager_plugins.hdfs_blob_manager.HDFSBlobManager',
            'blob_manager_config': {
                'hdfs_url': os.environ.get('blob_server.hdfs_url'),
                'hdfs_user': os.environ.get('blob_server.hdfs_user'),
                'root_directory': os.environ.get('blob_server.repo_name')
            }
        }
        blob_config = BlobConfig(config)
        blob_manager = BlobManagerFactory.create_blob_manager(blob_config.blob_manager_class(),
                                                              blob_config.blob_manager_config())
        uploaded_path = blob_manager.upload(_TMP_FILE)
        self.assertEqual(os.path.join(os.environ.get('blob_server.repo_name'), os.path.basename(_TMP_FILE)),
                         uploaded_path)

        downloaded_path = blob_manager.download(uploaded_path, _TMP_FOLDER)
        self.assertEqual(os.path.join(_TMP_FOLDER, os.path.basename(_TMP_FILE)), downloaded_path)


if __name__ == '__main__':
    unittest.main()
