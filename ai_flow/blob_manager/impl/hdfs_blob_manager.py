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
import fcntl
import os
import time
from typing import Dict, Any
from hdfs.client import InsecureClient

from ai_flow.blob_manager.blob_manager_interface import BlobManager
from ai_flow.common.exception.exceptions import AIFlowException, AIFlowConfigException


class HDFSBlobManager(BlobManager):
    """
    HDFSBlobManager is an implementation of BlobManager based on the hdfs file system
    HDFSBlobManager contains configuration items:
    1. hdfs_url: Hostname or IP address of HDFS namenode, prefixed with protocol, followed by WebHDFS port on namenode
    2. hdfs_user: User default. Defaults to the current user's (as determined by `whoami`).
    3. root_directory: The upload directory of the project.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not self.root_dir:
            raise AIFlowConfigException('`root_directory` option of blob manager config is not configured.')
        hdfs_url = config.get('hdfs_url', None)
        if not hdfs_url:
            raise AIFlowConfigException('`hdfs_url` is not configured.')
        hdfs_user = config.get('hdfs_user', 'default')
        hdfs_client = InsecureClient(url=hdfs_url, user=hdfs_user)
        self._hdfs_client = hdfs_client

    def upload(self, local_file_path: str) -> str:
        """
        Upload a given file to blob server. Uploaded file will be placed under self.root_dir.

        :param local_file_path: the path of file to be uploaded.
        :return the uri of the uploaded file in blob server.
        """
        file_name = os.path.basename(local_file_path)
        remote_file_path = os.path.join(self.root_dir, file_name)
        self._hdfs_client.upload(hdfs_path=remote_file_path, local_path=local_file_path)
        return remote_file_path

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
        local_file_path = os.path.join(local_dir, file_name)

        if not os.path.exists(local_file_path):
            lock_file_path = "{}.lock".format(local_file_path)
            lock_file = open(lock_file_path, 'w')
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                if not os.path.exists(local_file_path):
                    self.log.info("Downloading file from HDFS: {}".format(remote_file_path))
                    self._download_file_from_hdfs(hdfs_path=remote_file_path, local_path=local_file_path)
            except Exception as e:
                self.log.error("Failed to download file: {}".format(remote_file_path), exc_info=e)
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
            self.log.debug("HDFS file: {} already exist at {}".format(remote_file_path, local_file_path))
        return local_file_path

    def _download_file_from_hdfs(self, hdfs_path, local_path, retry_sleep_sec=5):
        for i in range(3):
            try:
                self._hdfs_client.download(hdfs_path=hdfs_path, local_path=local_path)
                return
            except Exception as e:
                self.log.error("Downloading file {} failed, retrying {}/3 in {} second".format(
                    hdfs_path, i+1, retry_sleep_sec), exc_info=e)
                time.sleep(retry_sleep_sec)
        raise RuntimeError("Failed to download HDFS file: {}".format(hdfs_path))

    def _check_remote_path_legality(self, file_path: str):
        """
        Check if the file can be downloaded by blob manager.

        :param file_path: The path of file to be checked.
        """
        if not file_path.startswith(self.root_dir):
            raise Exception("Cannot download {} from blob server".format(file_path))
