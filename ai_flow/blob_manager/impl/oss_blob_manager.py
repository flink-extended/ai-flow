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
import os
import fcntl
import time
from typing import Dict, Any
import oss2

from ai_flow.blob_manager.blob_manager_interface import BlobManager
from ai_flow.common.exception.exceptions import AIFlowException, AIFlowConfigException


class OssBlobManager(BlobManager):
    """
    OssBlobManager is an implementation of BlobManager based on the oss file system
    OssBlobManager contains configuration items:
    1. access_key_id: The oss access key.
    2. access_key_secret: The oss access secret.
    3. bucket: The oss bucket name.
    4. root_directory: The upload directory of the project.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not self.root_dir:
            raise AIFlowConfigException('`root_directory` option of blob manager config is not configured.')
        self.ack_id = config.get('access_key_id', None)
        self.ack_secret = config.get('access_key_secret', None)
        self.endpoint = config.get('endpoint', None)
        self.bucket_name = config.get('bucket', None)
        self._bucket = None

    def upload(self, local_file_path: str) -> str:
        """
        Upload a given file to blob server. Uploaded file will be placed under self.root_dir.

        :param local_file_path: the path of file to be uploaded.
        :return the uri of the uploaded file in blob server.
        """
        file_name = os.path.basename(local_file_path)
        remote_file_path = os.path.join(self.root_dir, file_name)
        self.bucket.put_object_from_file(key=remote_file_path, filename=local_file_path)
        return self._get_absolute_uri(remote_file_path)

    def download(self, remote_file_path: str, local_dir: str) -> str:
        """
        Download file from remote blob server to local directory.
        Only files located in self.root_dir can be downloaded by BlobManager.

        :param remote_file_path: The path of file to be downloaded.
        :param local_dir: the local directory.
        :return the local uri of the downloaded file.
        """
        self._check_remote_path_legality(remote_file_path)
        file_name = os.path.basename(remote_file_path)
        oss_object_key = remote_file_path.split("/", 1)[1]
        local_file_path = os.path.join(local_dir, file_name)
        if not os.path.exists(local_file_path):
            self.log.debug("{} not exist".format(local_file_path))
            lock_file_path = os.path.join(local_dir, "{}.lock".format(file_name))
            lock_file = open(lock_file_path, 'w')
            self.log.debug("Locking file {}".format(lock_file_path))
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            self.log.debug("Locked file {}".format(lock_file_path))
            try:
                if not os.path.exists(local_file_path):
                    self.log.info("Downloading oss object: {}".format(oss_object_key))
                    self._get_oss_object(local_file_path, oss_object_key)
            except Exception as e:
                self.log.error("Failed to download oss file: {}".format(oss_object_key), exc_info=e)
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                self.log.debug('Unlocked file {}'.format(lock_file_path))
                lock_file.close()
                if os.path.exists(lock_file_path):
                    try:
                        os.remove(lock_file_path)
                    except OSError as e:
                        self.log.warning("Failed to remove lock file: {}".format(lock_file_path), exc_info=e)
        else:
            self.log.debug("Oss file: {} already exist at {}".format(oss_object_key, local_file_path))
        return local_file_path

    @property
    def bucket(self):
        if self._bucket:
            return self._bucket
        auth = oss2.Auth(self.ack_id, self.ack_secret)
        self._bucket = oss2.Bucket(auth, self.endpoint, self.bucket_name)
        return self._bucket

    def _get_oss_object(self, dest, oss_object_key, retry_sleep_sec=5):
        for i in range(3):
            try:
                self.bucket.get_object_to_file(oss_object_key, filename=dest)
                return
            except Exception as e:
                self.log.error("Downloading object {} failed, retrying {}/3 in {} second".format(
                    oss_object_key, i+1, retry_sleep_sec), exc_info=e)
                time.sleep(retry_sleep_sec)
        raise RuntimeError("Failed to download oss file: {}".format(oss_object_key))

    def _check_remote_path_legality(self, file_path: str):
        """
        Check if the file can be downloaded by blob manager.

        :param file_path: The path of file to be checked.
        """
        absolute_root_dir = self._get_absolute_uri(self.root_dir)
        if not file_path.startswith(absolute_root_dir):
            raise Exception("Cannot download {} from blob server".format(file_path))

    def _get_absolute_uri(self, path):
        return '{}.{}/{}'.format(self.bucket_name, self.endpoint, path)
