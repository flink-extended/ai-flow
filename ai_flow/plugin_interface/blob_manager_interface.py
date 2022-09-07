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
import logging
from abc import ABC, abstractmethod
from typing import Text, Dict

from ai_flow.common.configuration import AIFlowConfiguration
from ai_flow.common.module_load import import_string


class BlobConfig(AIFlowConfiguration):

    def __init__(self, config: Dict):
        super().__init__()
        if config is None:
            raise Exception(
                'The `{}` option is not configured in the {} option. Please add it!'.format('blob', 'project.yaml'))
        self['blob_manager_class'] = None
        if config.get('blob_manager_class') is None:
            raise Exception(
                'The `blob_manager_class` option of blob config is not configured. '
                'Please add the `blob_manager_class` option under the `blob` option!')
        self['blob_manager_class'] = config.get('blob_manager_class')
        self['blob_manager_config'] = {}
        if config.get('blob_manager_config') is not None:
            self['blob_manager_config'] = config.get('blob_manager_config')


    def blob_manager_class(self):
        return self.get('blob_manager_class')

    def set_blob_manager_class(self, value):
        self['blob_manager_class'] = value

    def blob_manager_config(self):
        return self['blob_manager_config']

    def set_blob_manager_config(self, value):
        self['blob_manager_config'] = value


class BlobManager(ABC):
    """
    BlobManager is responsible for uploading and downloading files and resources for ai-flow projects.
    Every project should have its own BlobManager to store resources, all resources are uploaded to
    root directory of BlobManager.

    """
    def __init__(self, config: Dict):
        self._log = logging.getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)
        self.config = config
        self.root_dir = config.get('root_directory')

    @property
    def log(self) -> logging.Logger:
        return self._log

    @abstractmethod
    def upload(self, local_file_path: Text) -> Text:
        """
        Upload a given file to blob server. Uploaded file will be placed under self.root_dir.

        :param local_file_path: the path of file to be uploaded.
        :return the uri of the uploaded file in blob server.
        """
        pass

    @abstractmethod
    def download(self, remote_file_path: Text, local_dir: Text) -> Text:
        """
        Download file from remote blob server to local directory.
        Only files located in self.root_dir can be downloaded by BlobManager.

        :param remote_file_path: The path of file to be downloaded.
        :param local_dir: the local directory.
        :return the local uri of the downloaded file.
        """
        pass


class BlobManagerFactory:
    @classmethod
    def create_blob_manager(cls, class_name, config: Dict) -> BlobManager:
        """
        :param class_name: The class name of a (~class:`ai_flow.plugin_interface.blob_manager_interface.BlobManager`)
        :param config: The configuration of the BlobManager.
        """
        if class_name is None:
            return None
        class_object = import_string(class_name)
        return class_object(config)
