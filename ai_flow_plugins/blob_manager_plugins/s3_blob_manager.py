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
import fcntl
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Text, Dict, Any

import boto3
from botocore.config import Config

from ai_flow.plugin_interface.blob_manager_interface import BlobManager
from ai_flow.util.file_util.zip_file_util import make_dir_zipfile
from ai_flow_plugins.blob_manager_plugins.blob_manager_utils import extract_project_zip_file

logger = logging.getLogger(__name__)


class S3BlobManager(BlobManager):
    """
    S3BlobManager is an implementation of BlobManager based on the S3 file system
    S3BlobManager contains configuration items:
    1. service_name: The name of a service, e.g. 's3' or 'ec2'.
    2. region_name: The name of the region associated with the client.
    3. api_version: The API version to use.
    4. use_ssl: Whether or not to use SSL.
    5. verify: Whether or not to verify SSL certificates.
    6. endpoint_url: The complete URL to use for the constructed client.
    7. access_key_id: The access key for your AWS account.
    8. secret_access_key: The secret key for your AWS account.
    9. session_token: The session key for your AWS account.
    10. config: Advanced client configuration options.
    11. bucket_name: The S3 bucket name.
    12. local_repository: It represents the root path of the downloaded project package.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.s3_client = boto3.client(service_name=config.get('service_name', None),
                                      region_name=config.get('region_name', None),
                                      api_version=config.get('api_version', None),
                                      use_ssl=config.get('use_ssl', None),
                                      verify=config.get('verify', None),
                                      endpoint_url=config.get('endpoint_url', None),
                                      aws_access_key_id=config.get('access_key_id', None),
                                      aws_secret_access_key=config.get('secret_access_key', None),
                                      aws_session_token=config.get('session_token', None),
                                      config=Config(**config.get('config', {})))
        self.bucket_name = config.get('bucket_name', None)
        self.local_repository = config.get('local_repository', None)

    def upload_project(self, workflow_snapshot_id: Text, project_path: Text) -> Text:
        """
        Uploads a given project to blob server for remote execution.

        :param workflow_snapshot_id: It is the unique identifier for each workflow generation.
        :param project_path: The path of this project.
        :return The uri of the uploaded project file in blob server.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_file_name = 'workflow_{}_project.zip'.format(workflow_snapshot_id)
            temp_dir_path = Path(temp_dir)
            zip_file_path = temp_dir_path / zip_file_name
            make_dir_zipfile(project_path, zip_file_path)
            with open(zip_file_path, 'rb') as f:
                self.s3_client.upload_fileobj(f, self.bucket_name, zip_file_name)
        return zip_file_name

    def download_project(self, workflow_snapshot_id, remote_path: Text, local_path: Text = None) -> Text:
        """
        Downloads the needed resource from remote blob server to local process for remote execution.

        :param workflow_snapshot_id: It is the unique identifier for each workflow generation.
        :param remote_path: The project package uri.
        :param local_path: Download file root path.
        :return The local project path.
        """
        local_zip_file_name = 'workflow_{}_project'.format(workflow_snapshot_id)
        if local_path is not None:
            repo_path = Path(local_path)
        elif self.local_repository is not None:
            repo_path = Path(self.local_repository)
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
                    logger.info("Downloading S3 object: {}".format(remote_path))
                    self._get_s3_object(local_zip_file_path, remote_path)
                    logger.info("Downloaded S3 object: {}".format(local_zip_file_path))
            except Exception as e:
                logger.error("Failed to download S3 file: {}".format(remote_path), exc_info=e)
            finally:
                logger.debug('Locked file {}'.format(lock_file_path))
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                logger.debug('Unlocked file {}'.format(lock_file_path))
                lock_file.close()
                if os.path.exists(lock_file_path):
                    try:
                        os.remove(lock_file_path)
                    except OSError as e:
                        logger.warning("Failed to remove lock file: {}".format(lock_file_path), exc_info=e)
        else:
            logger.info("S3 file: {} already exist at {}".format(remote_path, local_zip_file_path))

        return extract_project_zip_file(workflow_snapshot_id=workflow_snapshot_id,
                                        local_root_path=repo_path,
                                        zip_file_path=local_zip_file_path,
                                        extract_project_path=extract_path)

    def _get_s3_object(self, local_path, object_key, retry_sleep_sec=5):
        for i in range(3):
            try:
                with open(local_path, 'wb') as f:
                    self.s3_client.download_fileobj(self.bucket_name, object_key, f)
                    return
            except Exception as e:
                logger.error("Downloading object {} failed, retrying {}/3 in {} second".format(object_key, i + 1,
                                                                                               retry_sleep_sec),
                             exc_info=e)
                time.sleep(retry_sleep_sec)
        raise RuntimeError("Failed to download S3 file: {}".format(object_key))
