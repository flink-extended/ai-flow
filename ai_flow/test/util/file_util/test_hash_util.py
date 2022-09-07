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

from ai_flow.util.file_util.hash_util import generate_file_md5


class TestHashUtil(unittest.TestCase):

    def test_generate_file_md5(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with open(os.path.join(tmp_dir, '1'), 'w') as f:
                f.write('abc')
            md51 = generate_file_md5(os.path.join(tmp_dir, '1'))
            with open(os.path.join(tmp_dir, '2'), 'w') as f:
                f.write('abc')
            md52 = generate_file_md5(os.path.join(tmp_dir, '2'))
            with open(os.path.join(tmp_dir, '3'), 'w') as f:
                f.write('a bc')
            md53 = generate_file_md5(os.path.join(tmp_dir, '3'))
        self.assertEquals(md51, md52)
        self.assertNotEquals(md51, md53)
