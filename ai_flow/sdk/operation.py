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
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import List

from ai_flow.common.util import serialization_utils

from ai_flow.blob_manager.blob_manager_interface import BlobManagerFactory, BlobManagerConfig
from ai_flow.common.configuration import config_constants
from ai_flow.common.util.module_utils import load_module
from ai_flow.common.util.file_util.hash_util import generate_file_md5
from ai_flow.common.util.file_util.zip_file_util import make_dir_zipfile
from ai_flow.model.workflow import Workflow

logger = logging.getLogger(__name__)


class WorkflowMeta(object):
    pass


def upload_workflows(workflow_file_path: str,
                     artifacts: List[str] = None,
                     namespace: str = 'default') -> List[WorkflowMeta]:
    """
    :param workflow_file_path: The path of the workflow to be uploaded.
    :param artifacts: The artifacts that the workflow needed.
    :param namespace: The namespace which the workflow is uploaded to.
    :return: The uploaded workflows.
    """
    workflows = _extract_workflows(workflow_file_path)
    file_hash, uploaded_path = _upload_snapshot(workflow_file_path, artifacts)
    for workflow in workflows:
        pickle = serialization_utils.serialize(workflow)
        _register_or_update_workflow_and_snapshot()


def _register_or_update_workflow_and_snapshot():
    # TODO fill up it after the meta and rpc module finished
    pass


def _upload_snapshot(file_path: str,
                     artifacts: List[str] = None):
    """
    Uploads the given workflow file along with artifacts to blob server.

    :param file_path: The path of workflow file.
    :param artifacts: The artifacts to be uploaded, only local file is allowed.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        filename, _ = os.path.splitext(os.path.split(file_path)[-1])
        dest_dir = Path(temp_dir) / filename
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, dest_dir)
        if artifacts is not None:
            for file in artifacts:
                shutil.copy2(file, dest_dir)

        zip_file_name = '{}.zip'.format(filename)
        zip_file_path = Path(temp_dir) / zip_file_name
        make_dir_zipfile(dest_dir, zip_file_path)
        file_hash = generate_file_md5(zip_file_path)

        blob_manager = BlobManagerFactory.create_blob_manager(BlobManagerConfig(config_constants.BLOB_MANAGER))
        uploaded_path = blob_manager.upload(local_file_path=zip_file_path)

        return file_hash, uploaded_path


def _extract_workflows(file_path: str) -> List[Workflow]:
    """
    Extract the top level workflow objects from the given python file.

    :param file_path: The file to be extracted
    :return: The list of workflow objects
    """
    if file_path is None or not os.path.isfile(file_path):
        return []
    try:
        mod = load_module(file_path)
    except Exception:
        logger.exception("Failed to import: %s", file_path)
        raise
    workflows = [o for o in list(mod.__dict__.values()) if isinstance(o, Workflow)]
    return workflows
