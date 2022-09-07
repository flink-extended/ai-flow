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
import logging
from typing import Optional, List

from ai_flow.common.exception.exceptions import AIFlowException
from ai_flow.rpc.client.aiflow_client import get_scheduler_client

from ai_flow.metadata.namespace import NamespaceMeta

logger = logging.getLogger(__name__)


def add_namespace(name: str, properties: dict) -> NamespaceMeta:
    """
    Creates a new namespace in metadata.

    :param name: The name of namespace to be added.
    :param properties: The properties of namespace.
    :return: The NamespaceMeta instance just added.
    """
    client = get_scheduler_client()
    return client.add_namespace(name, properties)


def get_namespace(name: str) -> Optional[NamespaceMeta]:
    """
    Retrieves the namespace from metadata.

    :param name: The name of namespace.
    :return: The NamespaceMeta instance, return None if no namespace found.
    """
    client = get_scheduler_client()
    return client.get_namespace(name)


def update_namespace(name: str, properties: dict) -> Optional[NamespaceMeta]:
    """
    Updates the properties of the namespace.

    :param name: The name of namespace to be updated.
    :param properties: The properties of namespace.
    :return: The NamespaceMeta instance just updated, return None if no namespace found.
    """
    client = get_scheduler_client()
    return client.update_namespace(name=name, properties=properties)


def list_namespace(limit: int = None, offset: int = None) -> Optional[List[NamespaceMeta]]:
    """
    Retrieves the list of namespaces from metadata.

    :param limit: The maximum records to be listed.
    :param offset: The offset to start to list.
    :return: The NamespaceMeta list, return None if no namespace found.
    """
    client = get_scheduler_client()
    return client.list_namespaces(page_size=limit, offset=offset)


def delete_namespace(name: str):
    """
    Deletes the namespace from metadata.

    :param name: The name of namespace.
    :raises: AIFlowException if failed to delete namespace.
    """
    client = get_scheduler_client()
    try:
        client.delete_namespace(name)
    except AIFlowException as e:
        logger.exception("Failed to delete namespace %s with exception %s", name, str(e))
        raise e
