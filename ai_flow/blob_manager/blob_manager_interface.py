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
import logging
from abc import ABC, abstractmethod
from typing import Dict

from ai_flow.common.exception.exceptions import AIFlowConfigException

from ai_flow.common.configuration import config_constants
from ai_flow.common.util.module_utils import import_string


class BlobManager(ABC):
    """
    BlobManager is responsible for uploading and downloading files and resources for AIFlow workflow.
    Every workflow should have its own BlobManager to store resources.
    Depends on the type of underlying storage, usually the BlobManager has a root directory, which is used
    to save all uploaded resources.
    """
    def __init__(self, config: Dict):
        self._log = logging.getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)
        self.config = config
        self.root_dir = config.get('root_directory')

    @property
    def log(self) -> logging.Logger:
        return self._log

    @abstractmethod
    def upload(self, local_file_path: str) -> str:
        """
        Upload a given file to blob server. Uploaded file will be placed under self.root_dir.

        :param local_file_path: the path of file to be uploaded.
        :return the uri of the uploaded file in blob server.
        """
        pass

    @abstractmethod
    def download(self, remote_file_path: str, local_dir: str) -> str:
        """
        Download file from remote blob server to local directory.
        Only files located in self.root_dir can be downloaded by BlobManager.

        :param remote_file_path: The path of file to be downloaded.
        :param local_dir: the local directory.
        :return the local uri of the downloaded file.
        """
        pass


class BlobManagerConfig:

    def __init__(self, config: Dict):
        if config is None:
            raise AIFlowConfigException('The blob manager option is not configured.')
        if config.get('blob_manager_class') is None:
            raise AIFlowConfigException('The `blob_manager_class` option of blob config is not configured.')
        self.config = config

    def get_class(self):
        return self.config.get('blob_manager_class')

    def get_customized_config(self):
        return self.config.get('blob_manager_config')


class BlobManagerFactory:

    @classmethod
    def get_default_blob_manager(cls) -> BlobManager:
        cls.create_blob_manager(config_constants.BLOB_MANAGER)

    @classmethod
    def create_blob_manager(cls, config: BlobManagerConfig) -> BlobManager:
        """
        :param config: The configuration of the BlobManager.
        """
        class_name = config.get_class()
        customized_config = config.get_customized_config()
        if class_name is None:
            return None
        class_object = import_string(class_name)
        return class_object(customized_config)
