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
import logging
import os
import time
from typing import Dict, Any

import boto3
from botocore.config import Config

from ai_flow.blob_manager.blob_manager_interface import BlobManager

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

    def upload(self, local_file_path: str) -> str:
        """
        Upload a given file to blob server.

        :param local_file_path: the path of file to be uploaded.
        :return the uri of the uploaded file in blob server.
        """
        file_name = os.path.basename(local_file_path)
        with open(local_file_path, 'rb') as f:
            self.s3_client.upload_fileobj(f, self.bucket_name, file_name)
        return file_name

    def download(self, remote_file_path: str, local_dir: str) -> str:
        """
        Download file from remote blob server to local directory.

        :param remote_file_path: The path of file to be downloaded.
        :param local_dir: the local directory.
        :return the local uri of the downloaded file.
        """
        file_name = os.path.basename(remote_file_path)
        local_file_path = os.path.join(local_dir, file_name)

        if not os.path.exists(local_file_path):
            lock_file_path = os.path.join(local_dir, "{}.lock".format(file_name))
            lock_file = open(lock_file_path, 'w')
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                if not os.path.exists(local_file_path):
                    self.log.info("Downloading S3 object: {}".format(remote_file_path))
                    self._get_s3_object(local_file_path, remote_file_path)
            except Exception as e:
                self.log.error("Failed to download S3 object: {}".format(remote_file_path), exc_info=e)
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
                if os.path.exists(lock_file_path):
                    try:
                        os.remove(lock_file_path)
                    except OSError as e:
                        self.log.warning("Failed to remove lock file: {}".format(lock_file_path), exc_info=e)
        else:
            self.log.debug("S3 file: {} already exist at {}".format(remote_file_path, local_file_path))
        return local_file_path

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
