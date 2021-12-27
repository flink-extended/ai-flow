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
import tempfile
import unittest
from unittest.mock import patch

from ai_flow.util.file_util.zip_file_util import make_file_zipfile, make_dir_zipfile, extract_zip_file


class TestZipFileUtil(unittest.TestCase):

    def test_unzip_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with open(os.path.join(tmp_dir, '1'), 'w') as f:
                f.write('abc')
            os.makedirs(os.path.join(tmp_dir, 'dir'))
            make_file_zipfile(os.path.join(tmp_dir, '1'), os.path.join(tmp_dir, '1.zip'))
            make_dir_zipfile(os.path.join(tmp_dir, 'dir'), os.path.join(tmp_dir, 'dir.zip'))

            self.assertTrue(os.path.exists(os.path.join(tmp_dir, '1.zip')))
            self.assertTrue(os.path.exists(os.path.join(tmp_dir, 'dir.zip')))

            with patch("zipfile.ZipFile.extractall") as zip_mock:
                extract_zip_file(os.path.join(tmp_dir, '1.zip'), os.path.join(tmp_dir, '1'))
                zip_mock.assert_not_called()
                extract_zip_file(os.path.join(tmp_dir, '1.zip'), os.path.join(tmp_dir, '2'))
                zip_mock.assert_called_once()

            with patch("zipfile.ZipFile.extractall") as zip_mock2:
                extract_zip_file(os.path.join(tmp_dir, 'dir.zip'), tmp_dir)
                zip_mock2.assert_not_called()
                extract_zip_file(os.path.join(tmp_dir, 'dir.zip'), os.path.join(tmp_dir, 'dir2'))
                zip_mock2.assert_called_once()


