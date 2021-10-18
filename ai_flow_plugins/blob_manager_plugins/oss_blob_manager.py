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
import logging
import tempfile
import fcntl
import time
from typing import Text, Dict, Any
from pathlib import Path
import oss2
from ai_flow.plugin_interface.blob_manager_interface import BlobManager
from ai_flow.util.file_util.zip_file_util import make_dir_zipfile
from ai_flow_plugins.blob_manager_plugins.blob_manager_utils import extract_project_zip_file

logger = logging.getLogger(__name__)


class OssBlobManager(BlobManager):
    """
    OssBlobManager is an implementation of BlobManager based on the oss file system
    OssBlobManager contains configuration items:
    1. access_key_id: The oss access key.
    2. access_key_secret: The oss access secret.
    3. bucket: The oss bucket name.
    4. local_repository: It represents the root path of the downloaded project package.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.ack_id = config.get('access_key_id', None)
        self.ack_secret = config.get('access_key_secret', None)
        self.endpoint = config.get('endpoint', None)
        self.bucket_name = config.get('bucket', None)
        self._bucket = None
        self.repo_name = config.get('repo_name', '')
        self._local_repo = config.get('local_repository', None)

    def upload_project(self, workflow_snapshot_id: Text, project_path: Text) -> Text:
        """
        upload a given project to blob server for remote execution.

        :param workflow_snapshot_id: It is the unique identifier for each workflow generation.
        :param project_path: The path of this project.
        :return The uri of the uploaded project file in blob server.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_file_name = 'workflow_{}_project.zip'.format(workflow_snapshot_id)
            temp_dir_path = Path(temp_dir)
            zip_file_path = temp_dir_path / zip_file_name
            make_dir_zipfile(project_path, zip_file_path)
            object_key = self.repo_name + '/' + zip_file_name
            self.bucket.put_object_from_file(key=object_key, filename=str(zip_file_path))
        return object_key

    def download_project(self, workflow_snapshot_id, remote_path: Text, local_path: Text = None) -> Text:
        """
        download the needed resource from remote blob server to local process for remote execution.

        :param workflow_snapshot_id: It is the unique identifier for each workflow generation.
        :param remote_path: The project package uri.
        :param local_path: Download file root path.
        :return The local project path.
        """
        local_zip_file_name = 'workflow_{}_project'.format(workflow_snapshot_id)
        oss_object_key = remote_path
        if local_path is not None:
            repo_path = Path(local_path)
        elif self._local_repo is not None:
            repo_path = Path(self._local_repo)
        else:
            repo_path = Path(tempfile.gettempdir())
        local_zip_file_path = str(repo_path / local_zip_file_name) + '.zip'
        extract_path = str(repo_path / local_zip_file_name)

        if not os.path.exists(local_zip_file_path):
            logger.debug("{} not exist".format(local_zip_file_path))
            lock_file_path = os.path.join(repo_path, "{}.lock".format(local_zip_file_name))
            lock_file = open(lock_file_path, 'w')
            logger.debug("Locking file {}".format(lock_file_path))
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            logger.debug("Locked file {}".format(lock_file_path))
            try:
                if not os.path.exists(local_zip_file_path):
                    logger.info("Downloading oss object: {}".format(oss_object_key))
                    self._get_oss_object(local_zip_file_path, oss_object_key)
            except Exception as e:
                logger.error("Failed to download oss file: {}".format(oss_object_key), exc_info=e)
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                logger.debug('Unlocked file {}'.format(lock_file_path))
                lock_file.close()
                if os.path.exists(lock_file_path):
                    try:
                        os.remove(lock_file_path)
                    except OSError as e:
                        logger.warning("Failed to remove lock file: {}".format(lock_file_path), exc_info=e)
        else:
            logger.info("Oss file: {} already exist at {}".format(oss_object_key, local_zip_file_path))

        return extract_project_zip_file(workflow_snapshot_id=workflow_snapshot_id,
                                        local_root_path=repo_path,
                                        zip_file_path=local_zip_file_path,
                                        extract_project_path=extract_path)

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
                logger.error("Downloading object {} failed, retrying {}/3 in {} second".format(oss_object_key, i+1,
                                                                                               retry_sleep_sec),
                             exc_info=e)
                time.sleep(retry_sleep_sec)
        raise RuntimeError("Failed to download oss file: {}".format(oss_object_key))
