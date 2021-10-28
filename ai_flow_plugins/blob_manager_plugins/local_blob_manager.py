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
import os
import shutil
from typing import Text, Dict, Any
from ai_flow.plugin_interface.blob_manager_interface import BlobManager


class LocalBlobManager(BlobManager):
    """
    LocalBlobManager is an implementation of BlobManager based on the local file system.
    LocalBlobManager contains 2 configuration items:
    1. local_repository: It represents the root path of the downloaded project package.
                         If local_path is set, local_path is used first.
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

    def upload(self, local_file_path: Text) -> Text:
        """
        Upload a given file to blob server. Uploaded file will be placed under self.root_dir.

        :param local_file_path: the path of file to be uploaded.
        :return the uri of the uploaded file in blob server.
        """
        dest_dir = self.root_dir
        if dest_dir:
            file_name = os.path.basename(local_file_path)
            dest_path = os.path.join(dest_dir, file_name)
            shutil.move(local_file_path, dest_path)
            return dest_path
        else:
            return local_file_path

    def download(self, remote_file_path: Text, local_dir: Text = None) -> Text:
        """
        Download file from remote blob server to local directory.
        Only files located in self.root_dir can be downloaded by BlobManager.

        :param remote_file_path: The path of file to be downloaded.
        :param local_dir: the local directory.
        :return the local uri of the downloaded file.
        """
        self._check_remote_path_legality(remote_file_path)
        if local_dir is not None:
            file_name = os.path.basename(remote_file_path)
            dest_path = os.path.join(local_dir, file_name)
            if remote_file_path != dest_path:
                shutil.copy(remote_file_path, dest_path)
            return dest_path
        else:
            return remote_file_path

    def _check_remote_path_legality(self, file_path: Text):
        """
        Check if the file can be downloaded by blob manager.

        :param file_path: The path of file to be checked.
        """
        if not file_path.startswith(self.root_dir):
            raise Exception("Cannot download {} from blob server".format(file_path))
