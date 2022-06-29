## Copyright 2022 The AI Flow Authors
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
from ai_flow.common.result import BaseResult, RetCode
from ai_flow.rpc.service.util.meta_to_proto import MetaToProto
from ai_flow.rpc.service.util.response_wrapper import catch_exception, wrap_data_response, wrap_namespace_list_response, \
    wrap_result_response, wrap_workflow_snapshot_list_response
from ai_flow.metadata.metadata_manager import MetadataManager
from ai_flow.common.util.db_util.session import create_session
from ai_flow.rpc.protobuf import metadata_service_pb2_grpc


class MetadataService(metadata_service_pb2_grpc.MetadataServiceServicer):

    @catch_exception
    def addNamespace(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            properties = {}
            if request.properties is not None:
                for key, val in request.properties.items():
                    properties.update({key: val})
            namespace = metadata_manager.add_namespace(request.name, properties)
            return wrap_data_response(MetaToProto.namespace_meta_to_proto(namespace))

    @catch_exception
    def getNamespace(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            namespace = metadata_manager.get_namespace(request.name)
            return wrap_data_response(MetaToProto.namespace_meta_to_proto(namespace))

    @catch_exception
    def updateNamespace(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            namespace = metadata_manager.get_namespace(request.name)
            if namespace is None:
                response = None
            else:
                properties = {}
                if request.properties is not None:
                    for key, val in request.properties.items():
                        properties.update({key: val})
                namespace = metadata_manager.update_namespace(request.name, properties)
                response = MetaToProto.namespace_meta_to_proto(namespace)
            return wrap_data_response(response)

    @catch_exception
    def listNamespaces(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            namespaces = metadata_manager.list_namespace(page_size=request.page_size,
                                                         offset=request.offset)
            return wrap_namespace_list_response(MetaToProto.namespace_meta_list_to_proto(namespaces))

    @catch_exception
    def deleteNamespace(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            namespace = metadata_manager.get_namespace(request.name)
            if namespace is None:
                return wrap_result_response(BaseResult(RetCode.ERROR, f'Namespace {request.name} not exists.'))
            else:
                metadata_manager.delete_namespace(request.name)
                return wrap_result_response(BaseResult(RetCode.OK, None))

    @catch_exception
    def addWorkflowSnapshot(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            uri = request.uri.value if request.HasField('uri') else None
            signature = request.signature.value if request.HasField('signature') else None
            workflow_snapshot = metadata_manager.add_workflow_snapshot(
                request.workflow_id, uri, request.workflow_object, signature)
            return wrap_data_response(MetaToProto.workflow_snapshot_meta_to_proto(workflow_snapshot))

    @catch_exception
    def getWorkflowSnapshot(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflow_snapshot = metadata_manager.get_workflow_snapshot(request.id)
            return wrap_data_response(MetaToProto.workflow_snapshot_meta_to_proto(workflow_snapshot))

    @catch_exception
    def listWorkflowSnapshots(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            workflow_snapshots = metadata_manager.list_workflow_snapshots(workflow_id=request.workflow_id,
                                                                          page_size=request.page_size,
                                                                          offset=request.offset)
            return wrap_workflow_snapshot_list_response(
                MetaToProto.workflow_snapshot_meta_list_to_proto(workflow_snapshots))

    @catch_exception
    def deleteWorkflowSnapshot(self, request, context):
        with create_session() as session:
            metadata_manager = MetadataManager(session)
            snapshot = metadata_manager.get_workflow_snapshot(request.id)
            if snapshot is None:
                return wrap_result_response(BaseResult(RetCode.ERROR, f'Workflow snapshot {request.id} not exists'))
            else:
                metadata_manager.delete_workflow_snapshot(request.id)
                return wrap_result_response(BaseResult(RetCode.OK, None))


