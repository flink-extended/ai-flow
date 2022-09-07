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
import threading
import shutil
import unittest
from unittest import mock

import os

from ai_flow.blob_manager.blob_manager_interface import BlobManagerFactory, BlobManagerConfig
from ai_flow.blob_manager.impl.oss_blob_manager import OssBlobManager

_TMP_FOLDER = '/tmp/' + __name__
_TMP_FILE = os.path.join(_TMP_FOLDER, 'file.txt')
CONFIG = BlobManagerConfig({
    'blob_manager_class': 'ai_flow.blob_manager.impl.oss_blob_manager.OssBlobManager',
    'blob_manager_config': {
        'endpoint': 'endpoint',
        'bucket': 'bucket',
        'root_directory': 'tmp'
    }
})


class TestOSSBlobManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        if not os.path.exists(_TMP_FOLDER):
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

    def test_without_root_directory_set(self):
        config = BlobManagerConfig({
            'blob_manager_class': 'ai_flow.blob_manager.impl.oss_blob_manager.OssBlobManager',
            'blob_manager_config': {}
        })
        with self.assertRaisesRegex(Exception, '`root_directory` option of blob manager config is not configured'):
            BlobManagerFactory.create_blob_manager(config)

    @unittest.skipUnless((os.environ.get('blob_server.endpoint') is not None
                          and os.environ.get('blob_server.access_key_id') is not None
                          and os.environ.get('blob_server.access_key_secret') is not None
                          and os.environ.get('blob_server.bucket') is not None
                          and os.environ.get('blob_server.repo_name') is not None), 'need set oss')
    def test_project_upload_download_oss(self):
        config = BlobManagerConfig({
            'blob_manager_class': 'ai_flow.blob_manager.impl.oss_blob_manager.OssBlobManager',
            'blob_manager_config': {
                'access_key_id': os.environ.get('blob_server.access_key_id'),
                'access_key_secret': os.environ.get('blob_server.access_key_secret'),
                'endpoint': os.environ.get('blob_server.endpoint'),
                'bucket': os.environ.get('blob_server.bucket'),
                'root_directory': os.environ.get('blob_server.repo_name')
            }
        })
        blob_manager = BlobManagerFactory.create_blob_manager(config)
        uploaded_path = blob_manager.upload(_TMP_FILE)
        self.assertEqual(os.path.join(os.environ.get('blob_server.repo_name'), os.path.basename(_TMP_FILE)),
                         uploaded_path)

        downloaded_path = blob_manager.download(uploaded_path, _TMP_FOLDER)
        self.assertEqual(os.path.join(_TMP_FOLDER, os.path.basename(_TMP_FILE)), downloaded_path)

    def test_download_oss_file_concurrently(self):
        project_zip = '/tmp/workflow_1_project.zip'
        if os.path.exists(project_zip):
            os.remove(project_zip)
        config = {
            'endpoint': 'endpoint',
            'bucket': 'bucket',
            'root_directory': 'tmp'
        }
        oss_blob_manager = OssBlobManager(config)

        zip_file_path = None
        call_count = 0

        def mock_get_oss_object(dest, oss_object_key):
            nonlocal zip_file_path, call_count
            call_count += 1
            zip_file_path = dest
            with open(dest, 'w') as f:
                pass

        oss_blob_manager._get_oss_object = mock_get_oss_object

        # get_oss_object_func = mock.patch.object(oss_blob_manager, '_get_oss_object', wraps=mock_get_oss_object)
        def download_loop():
            for i in range(1000):
                oss_blob_manager.download('bucket.endpoint/tmp/dummy', '/tmp')

        try:
            t1 = threading.Thread(target=download_loop)
            t1.start()

            download_loop()
            t1.join()

            self.assertEqual(1, call_count)
        finally:
            if zip_file_path is not None:
                os.remove(zip_file_path)

    def test_lazily_init_bucket(self):
        config = {'root_directory': 'oss://'}
        oss_blob_manager = OssBlobManager(config)
        self.assertIsNone(oss_blob_manager._bucket)

        with mock.patch('ai_flow.blob_manager.impl.oss_blob_manager.oss2') as mock_oss:
            mock_bucket = mock.Mock()
            mock_oss.Bucket.return_value = mock_bucket
            bucket = oss_blob_manager.bucket
            mock_oss.Auth.assert_called_once()
            mock_oss.Bucket.assert_called_once()
            self.assertEqual(mock_bucket, bucket)
            self.assertEqual(mock_bucket, oss_blob_manager.bucket)

    def test__get_oss_object_retry(self):
        config = {'root_directory': 'oss://'}

        oss_blob_manager = OssBlobManager(config)

        with mock.patch.object(oss_blob_manager, '_bucket') as mock_bucket:
            mock_bucket.get_object_to_file.side_effect = [RuntimeError("boom"), RuntimeError("boom"),
                                                          RuntimeError("boom")]
            with self.assertRaises(RuntimeError):
                oss_blob_manager._get_oss_object('dummy_dest', 'key', retry_sleep_sec=0.1)
                self.assertEqual(3, mock_bucket.get_object_to_file.call_count)

        with mock.patch.object(oss_blob_manager, '_bucket') as mock_bucket:
            mock_bucket.get_object_to_file.side_effect = [RuntimeError("boom"), None]
            oss_blob_manager._get_oss_object('dummy_dest', 'key', retry_sleep_sec=0.1)
            self.assertEqual(2, mock_bucket.get_object_to_file.call_count)


if __name__ == '__main__':
    unittest.main()

