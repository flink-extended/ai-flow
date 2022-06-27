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
import importlib
import logging
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import List, Optional

from ai_flow.common.configuration import config_constants

from ai_flow.blob_manager.blob_manager_interface import BlobManagerFactory, BlobManagerConfig
from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.common.util.file_util.hash_util import generate_file_md5
from ai_flow.common.util.file_util.zip_file_util import make_dir_zipfile, extract_zip_file
from ai_flow.common.util.module_utils import load_module
from ai_flow.metadata.workflow_snapshot import WorkflowSnapshotMeta

from ai_flow.metadata.workflow import WorkflowMeta

from ai_flow.common.util.db_util.session import create_session
from ai_flow.metadata.metadata_manager import MetadataManager
from ai_flow.model.workflow import Workflow

logger = logging.getLogger(__name__)


def get_workflow_snapshot(workflow_id) -> Optional[WorkflowSnapshotMeta]:
    """
    Get the location of the snapshot of the workflow execution

    :param workflow_id: Id of the workflow
    :return: The WorkflowSnapshotMeta
    """
    with create_session() as session:
        metadata_manager = MetadataManager(session)
        snapshot = metadata_manager.get_latest_snapshot(workflow_id)
        return snapshot


def get_workflow(workflow_execution_id) -> Optional[WorkflowMeta]:
    """
    Get the name of the workflow by the execution id

    :param workflow_execution_id: Id of the workflow execution
    :return: The WorkflowMeta
    """
    with create_session() as session:
        metadata_manager = MetadataManager(session)
        workflow_execution = metadata_manager.get_workflow_execution(workflow_execution_id)
        if workflow_execution is not None:
            workflow = metadata_manager.get_workflow_by_id(workflow_execution.workflow_id)
            return workflow
        else:
            return None


def upload_workflow_snapshot(file_path: str, artifacts: List[str] = None):
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


def extract_workflows_from_file(file_path: str) -> List[Workflow]:
    """
    Extract the top level workflow objects from the given python file.
    :param file_path: The file to be extracted
    :return: The list of workflow objects
    """
    if file_path is None or not os.path.isfile(file_path):
        raise AIFlowException(f"Cannot extract workflow because file not exists: {file_path}")
    try:
        mod = load_module(file_path)
    except Exception:
        logger.exception("Failed to import: %s", file_path)
        raise
    workflows = [o for o in list(mod.__dict__.values()) if isinstance(o, Workflow)]
    return workflows


def extract_workflows_from_zip(file_path: str, extract_path: str) -> List[Workflow]:
    """
    Extract the top level workflow objects from the given zip file.
    :param file_path: The zip file to be extracted
    :param extract_path: The path to place extracted files
    :return: The list of workflow objects
    """
    workflows = []
    root_path = extract_zip_file(file_path, extract_path)
    for file in os.listdir(root_path):
        abs_path = os.path.join(root_path, file)
        if os.path.isfile(abs_path):
            ws = extract_workflows_from_file(abs_path)
            workflows.extend(ws)
    return workflows

    #
    # workflows = []
    # current_zip_file = zipfile.ZipFile(file_path)
    # for zip_info in current_zip_file.infolist():
    #     print(zip_info)
    #     head, _ = os.path.split(zip_info.filename)
    #     mod_name, ext = os.path.splitext(zip_info.filename)
    #     if ext not in [".py", ".pyc"]:
    #         continue
    #     # if head:
    #     #     continue
    #
    #     if mod_name in sys.modules:
    #         del sys.modules[mod_name]
    #
    #     try:
    #         sys.path.insert(0, file_path)
    #         current_module = importlib.import_module(mod_name)
    #         ws = [o for o in list(current_module.__dict__.values()) if isinstance(o, Workflow)]
    #         workflows.extend(ws)
    #     except Exception as e:  # pylint: disable=broad-except
    #         logger.exception("Failed to import: %s", file_path)
    # return workflows


