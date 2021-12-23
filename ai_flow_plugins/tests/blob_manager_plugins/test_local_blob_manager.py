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
import os
import shutil
import threading
from ai_flow.plugin_interface.blob_manager_interface import BlobConfig, BlobManagerFactory


_TMP_FOLDER = '/tmp/' + __name__
_UPLOAD_FOLDER = os.path.join(_TMP_FOLDER, 'upload')
_DOWNLOAD_FOLDER = os.path.join(_TMP_FOLDER, 'download')
_TMP_FILE = os.path.join(_TMP_FOLDER, 'file.txt')


class TestLocalBlobManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        os.mkdir(_TMP_FOLDER)
        os.mkdir(_UPLOAD_FOLDER)
        os.mkdir(_DOWNLOAD_FOLDER)

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

    def test_without_root_directory_set(self):
        config = {
            'blob_manager_class': 'ai_flow_plugins.blob_manager_plugins.local_blob_manager.LocalBlobManager'
        }
        blob_config = BlobConfig(config)
        with self.assertRaisesRegex(Exception, '`root_directory` option of blob manager config is not configured'):
            BlobManagerFactory.create_blob_manager(blob_config.blob_manager_class(),
                                                   blob_config.blob_manager_config())


    def test_project_upload_download_local(self):
        config = {
            'blob_manager_class': 'ai_flow_plugins.blob_manager_plugins.local_blob_manager.LocalBlobManager',
            'blob_manager_config': {
                'root_directory': _UPLOAD_FOLDER
            }
        }
        blob_config = BlobConfig(config)
        blob_manager = BlobManagerFactory.create_blob_manager(blob_config.blob_manager_class(),
                                                              blob_config.blob_manager_config())
        uploaded_path = blob_manager.upload(_TMP_FILE)
        self.assertEqual(os.path.join(_UPLOAD_FOLDER, os.path.basename(_TMP_FILE), uploaded_path), uploaded_path)

        downloaded_path = blob_manager.download(uploaded_path, _DOWNLOAD_FOLDER)
        self.assertEqual(os.path.join(_DOWNLOAD_FOLDER, os.path.basename(_TMP_FILE)), downloaded_path)

    def test_project_upload_download_local_2(self):
        config = {
            'blob_manager_class': 'ai_flow_plugins.blob_manager_plugins.local_blob_manager.LocalBlobManager',
            'blob_manager_config': {
                'root_directory': _UPLOAD_FOLDER
            }
        }
        blob_config = BlobConfig(config)
        blob_manager = BlobManagerFactory.create_blob_manager(blob_config.blob_manager_class(),
                                                              blob_config.blob_manager_config())

        uploaded_path = blob_manager.upload(_TMP_FILE)
        downloaded_path = blob_manager.download(uploaded_path)
        self.assertEqual(uploaded_path, downloaded_path)

    def test_project_download_local_same_time(self):
        config = {
            'blob_manager_class': 'ai_flow_plugins.blob_manager_plugins.local_blob_manager.LocalBlobManager',
            'blob_manager_config': {
                'root_directory': _UPLOAD_FOLDER
            }
        }
        blob_config = BlobConfig(config)
        blob_manager = BlobManagerFactory.create_blob_manager(blob_config.blob_manager_class(),
                                                              blob_config.blob_manager_config())

        uploaded_path = blob_manager.upload(_TMP_FILE)

        def download_project():
            blob_manager.download(uploaded_path)

        t1 = threading.Thread(target=download_project, args=())
        t1.setDaemon(True)
        t1.start()
        t2 = threading.Thread(target=download_project, args=())
        t2.setDaemon(True)
        t2.start()
        t1.join()
        t2.join()
        downloaded_path = blob_manager.download(uploaded_path, _DOWNLOAD_FOLDER)
        self.assertEqual(os.path.join(_DOWNLOAD_FOLDER, os.path.basename(_TMP_FILE)), downloaded_path)


if __name__ == '__main__':
    unittest.main()
