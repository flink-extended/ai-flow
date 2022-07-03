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
from typing import Optional, List

import grpc
from ai_flow.metadata.workflow_snapshot import WorkflowSnapshotMeta
from ai_flow.metadata.namespace import NamespaceMeta

from ai_flow.rpc.client.util.response_unwrapper import unwrap_namespace_response, unwrap_namespace_list_response, \
    unwrap_bool_response, unwrap_workflow_snapshot_response, unwrap_workflow_snapshot_list_response
from ai_flow.rpc.protobuf import metadata_service_pb2_grpc
from ai_flow.rpc.protobuf.message_pb2 import NamespaceProto, NameRequest, ListRequest, WorkflowSnapshotProto, IdRequest
from ai_flow.rpc.protobuf.metadata_service_pb2 import ListWorkflowSnapshotsRequest
from ai_flow.rpc import string_value



class MetadataClient(object):
    def __init__(self, server_uri):
        channel = grpc.insecure_channel(server_uri)
        self.metadata_stub = metadata_service_pb2_grpc.MetadataServiceStub(channel)

    def add_namespace(self, name, properties: dict = None) -> Optional[NamespaceMeta]:
        request = NamespaceProto(name=name, properties=properties)
        response = self.metadata_stub.addNamespace(request)
        return unwrap_namespace_response(response)

    def get_namespace(self, name) -> Optional[NamespaceMeta]:
        request = NameRequest(name=name)
        response = self.metadata_stub.getNamespace(request)
        return unwrap_namespace_response(response)

    def update_namespace(self, name, properties) -> Optional[NamespaceMeta]:
        request = NamespaceProto(name=name, properties=properties)
        response = self.metadata_stub.updateNamespace(request)
        return unwrap_namespace_response(response)

    def list_namespaces(self, page_size=None, offset=None) -> Optional[List[NamespaceMeta]]:
        request = ListRequest(page_size=page_size, offset=offset)
        response = self.metadata_stub.listNamespaces(request)
        return unwrap_namespace_list_response(response)

    def delete_namespace(self, name) -> bool:
        request = NameRequest(name=name)
        response = self.metadata_stub.deleteNamespace(request)
        return unwrap_bool_response(response)

    def add_workflow_snapshot(self, workflow_id, uri, workflow_object, signature) -> Optional[WorkflowSnapshotMeta]:
        request = WorkflowSnapshotProto(workflow_id=workflow_id,
                                        workflow_object=workflow_object,
                                        uri=string_value(uri),
                                        signature=string_value(signature))
        response = self.metadata_stub.addWorkflowSnapshot(request)
        return unwrap_workflow_snapshot_response(response)

    def get_workflow_snapshot(self, workflow_snapshot_id) -> Optional[WorkflowSnapshotMeta]:
        request = IdRequest(id=workflow_snapshot_id)
        response = self.metadata_stub.getWorkflowSnapshot(request)
        return unwrap_workflow_snapshot_response(response)

    def list_workflow_snapshots(self, workflow_id, page_size=None, offset=None) -> Optional[List[WorkflowSnapshotMeta]]:
        request = ListWorkflowSnapshotsRequest(workflow_id=workflow_id,
                                               page_size=page_size,
                                               offset=offset)
        response = self.metadata_stub.listWorkflowSnapshots(request)
        return unwrap_workflow_snapshot_list_response(response)

    def delete_workflow_snapshot(self, workflow_snapshot_id) -> bool:
        request = IdRequest(id=workflow_snapshot_id)
        response = self.metadata_stub.deleteWorkflowSnapshot(request)
        return unwrap_bool_response(response)