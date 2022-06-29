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
from typing import List

from ai_flow.metadata.workflow_snapshot import WorkflowSnapshotMeta

from ai_flow.common.util.time_utils import parse_to_utc_date
from ai_flow.metadata.workflow import WorkflowMeta

from ai_flow.metadata.namespace import NamespaceMeta
from ai_flow.rpc.protobuf.message_pb2 import NamespaceProto, WorkflowProto, WorkflowSnapshotProto


class ProtoToMeta:

    @staticmethod
    def proto_to_namespace_meta(namespace_proto: NamespaceProto) -> NamespaceMeta:
        properties = {}
        if namespace_proto.properties != {}:
            for key, val in namespace_proto.properties.items():
                properties.update({key: val})
        return NamespaceMeta(name=namespace_proto.name,
                             properties=properties)

    @staticmethod
    def proto_to_namespace_meta_list(namespace_list_proto: List[NamespaceProto]) -> List[NamespaceMeta]:
        namespace_list = []
        for namespace_proto in namespace_list_proto:
            namespace_list.append(ProtoToMeta.proto_to_namespace_meta(namespace_proto))
        return namespace_list

    @staticmethod
    def proto_to_workflow_meta(workflow_proto: WorkflowProto) -> WorkflowMeta:
        create_time_epoch = workflow_proto.create_time.value if workflow_proto.HasField('create_time') else None
        update_time_epoch = workflow_proto.update_time.value if workflow_proto.HasField('update_time') else None
        event_offset = workflow_proto.event_offset.value if workflow_proto.HasField('event_offset') else None
        return WorkflowMeta(name=workflow_proto.name,
                            namespace=workflow_proto.namespace,
                            content=workflow_proto.content,
                            workflow_object=workflow_proto.pickled_workflow,
                            create_time=parse_to_utc_date(create_time_epoch),
                            update_time=parse_to_utc_date(update_time_epoch),
                            is_enabled=workflow_proto.is_enabled,
                            event_offset=event_offset,
                            uuid=workflow_proto.uuid)

    @staticmethod
    def proto_to_workflow_meta_list(workflow_list_proto: List[WorkflowProto]) -> List[WorkflowMeta]:
        workflow_list = []
        for workflow_proto in workflow_list_proto:
            workflow_list.append(ProtoToMeta.proto_to_workflow_meta(workflow_proto))
        return workflow_list

    @staticmethod
    def proto_to_workflow_snapshot_meta(
            workflow_snapshot_proto: List[WorkflowSnapshotProto]) -> List[WorkflowSnapshotMeta]:
        create_time_epoch = workflow_snapshot_proto.create_time.value \
            if workflow_snapshot_proto.HasField('create_time') else None
        uri = workflow_snapshot_proto.uri.value if workflow_snapshot_proto.HasField('uri') else None
        signature = workflow_snapshot_proto.signature.value if workflow_snapshot_proto.HasField('signature') else None
        return WorkflowSnapshotMeta(workflow_id=workflow_snapshot_proto.workflow_id,
                                    workflow_object=workflow_snapshot_proto.workflow_object,
                                    uri=uri,
                                    signature=signature,
                                    create_time=parse_to_utc_date(create_time_epoch),
                                    uuid=workflow_snapshot_proto.uuid)

    @staticmethod
    def proto_to_workflow_snapshot_meta_list(snapshot_list_proto: List[WorkflowSnapshotProto]) -> List[WorkflowSnapshotMeta]:
        snapshot_list = []
        for snapshot_proto in snapshot_list_proto:
            snapshot_list.append(ProtoToMeta.proto_to_workflow_snapshot_meta(snapshot_proto))
        return snapshot_list

