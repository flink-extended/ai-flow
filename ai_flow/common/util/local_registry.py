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
from dbm import dumb
import os

from ai_flow.common.exception.exceptions import AIFlowException


class LocalRegistry(object):
    """k-v store with string datatype based on local file."""

    def __init__(self,
                 file_path):
        self._db = None
        if not os.path.isdir(os.path.dirname(os.path.abspath(file_path))):
            raise AIFlowException('Parent directory of local registry not exists.')
        self._db = dumb.open(file_path, 'c')

    def set(self, key, value):
        self._db[str.encode(key)] = str(value)
        return self

    def get(self, key):
        if str.encode(key) in self._db.keys():
            return self._db[str.encode(key)]
        else:
            return None

    def sync(self):
        self._db.sync()

    def remove(self, key):
        if str.encode(key) in self._db.keys():
            del self._db[str.encode(key)]

    def __del__(self):
        if self._db:
            self._db.close()
