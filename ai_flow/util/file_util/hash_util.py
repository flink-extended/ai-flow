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
import hashlib


def generate_file_md5(file, chunk_size=2**20):
    file_hash = hashlib.md5()

    with open(file, "rb") as f:

        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            file_hash.update(chunk)
    return file_hash.hexdigest()
