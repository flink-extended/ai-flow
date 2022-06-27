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
from typing import List

from ai_flow.metadata.workflow_snapshot import WorkflowSnapshotMeta
from ai_flow.common.util.time_utils import datetime_to_epoch
from ai_flow.metadata.workflow import WorkflowMeta
from ai_flow.metadata.namespace import NamespaceMeta
from ai_flow.rpc.protobuf.message_pb2 import NamespaceProto, WorkflowProto, WorkflowSnapshotProto
from ai_flow.rpc import int64_value, string_value


class MetaToProto:
    @staticmethod
    def namespace_meta_to_proto(namespace: NamespaceMeta) -> NamespaceProto:
        if namespace is None:
            return None
        else:
            return NamespaceProto(name=namespace.name,
                                  properties=namespace.get_properties())

    @staticmethod
    def namespace_meta_list_to_proto(namespaces: List[NamespaceMeta]) -> List[NamespaceProto]:
        namespace_proto_list = []
        for namespace in namespaces:
            namespace_proto_list.append(MetaToProto.namespace_meta_to_proto(namespace))
        return namespace_proto_list

    @staticmethod
    def workflow_meta_to_proto(workflow: WorkflowMeta) -> WorkflowProto:
        if workflow is None:
            return None
        else:
            return WorkflowProto(uuid=workflow.id,
                                 name=workflow.name,
                                 namespace=workflow.namespace,
                                 content=workflow.content,
                                 pickled_workflow=workflow.workflow_object,
                                 create_time=int64_value(datetime_to_epoch(workflow.create_time)),
                                 update_time=int64_value(datetime_to_epoch(workflow.update_time)),
                                 is_enabled=workflow.is_enabled,
                                 event_offset=int64_value(workflow.event_offset))

    @staticmethod
    def workflow_meta_list_to_proto(workflows: List[WorkflowMeta]) -> List[WorkflowProto]:
        workflow_proto_list = []
        for workflow in workflows:
            workflow_proto_list.append(MetaToProto.workflow_meta_to_proto(workflow))
        return workflow_proto_list

    @staticmethod
    def workflow_snapshot_meta_to_proto(workflow_snapshot: WorkflowSnapshotMeta) -> WorkflowSnapshotProto:
        if workflow_snapshot is None:
            return None
        else:
            return WorkflowSnapshotProto(uuid=workflow_snapshot.id,
                                         workflow_id=workflow_snapshot.workflow_id,
                                         create_time=int64_value(datetime_to_epoch(workflow_snapshot.create_time)),
                                         workflow_object=workflow_snapshot.workflow_object,
                                         uri=string_value(workflow_snapshot.uri),
                                         signature=string_value(workflow_snapshot.signature))

    @staticmethod
    def workflow_snapshot_meta_list_to_proto(workflow_snapshots: List[WorkflowSnapshotMeta]) -> List[WorkflowSnapshotProto]:
        workflow_snapshot_proto_list = []
        for snapshot in workflow_snapshots:
            workflow_snapshot_proto_list.append(MetaToProto.workflow_snapshot_meta_to_proto(snapshot))
        return workflow_snapshot_proto_list



    # @staticmethod
    # def dataset_meta_to_proto(dataset_mata) -> DatasetMeta:
    #     if dataset_mata is None:
    #         return None
    #     else:
    #         if dataset_mata.schema is not None:
    #             name_list = dataset_mata.schema.name_list
    #             type_list = dataset_mata.schema.type_list
    #             data_type_list = []
    #             if type_list is not None:
    #                 for data_type in type_list:
    #                     data_type_list.append(DataTypeProto.Value(data_type))
    #             else:
    #                 data_type_list = None
    #         else:
    #             name_list = None
    #             data_type_list = None
    #         schema = SchemaProto(name_list=name_list,
    #                              type_list=data_type_list)
    #     return DatasetProto(
    #         uuid=dataset_mata.uuid,
    #         name=dataset_mata.name,
    #         properties=dataset_mata.properties,
    #         data_format=stringValue(dataset_mata.data_format),
    #         description=stringValue(dataset_mata.description),
    #         uri=stringValue(dataset_mata.uri),
    #         create_time=int64Value(dataset_mata.create_time),
    #         update_time=int64Value(dataset_mata.update_time),
    #         schema=schema,
    #         catalog_name=stringValue(dataset_mata.catalog_name),
    #         catalog_type=stringValue(dataset_mata.catalog_type),
    #         catalog_database=stringValue(dataset_mata.catalog_database),
    #         catalog_connection_uri=stringValue(dataset_mata.catalog_connection_uri),
    #         catalog_table=stringValue(dataset_mata.catalog_table))
    #
    # @staticmethod
    # def dataset_meta_list_to_proto(datasets: List[DatasetMeta]) -> List[DatasetProto]:
    #     list_dataset_proto = []
    #     for dataset in datasets:
    #         list_dataset_proto.append(MetaToProto.dataset_meta_to_proto(dataset))
    #     return list_dataset_proto
    #
    #
    #
    # @staticmethod
    # def workflow_meta_to_proto(workflow_meta: WorkflowMeta) -> WorkflowMetaProto:
    #     if workflow_meta is None:
    #         return None
    #     else:
    #         return WorkflowMetaProto(name=workflow_meta.name,
    #                                  project_id=int64Value(workflow_meta.project_id),
    #                                  properties=workflow_meta.properties,
    #                                  create_time=int64Value(workflow_meta.create_time),
    #                                  update_time=int64Value(workflow_meta.update_time),
    #                                  context_extractor_in_bytes=workflow_meta.context_extractor_in_bytes,
    #                                  graph=stringValue(workflow_meta.graph),
    #                                  uuid=workflow_meta.uuid)
    #
    # @staticmethod
    # def workflow_meta_list_to_proto(workflows: List[WorkflowMeta]) -> List[WorkflowMetaProto]:
    #     workflow_proto_list = []
    #     for workflow in workflows:
    #         workflow_proto_list.append(MetaToProto.workflow_meta_to_proto(workflow))
    #     return workflow_proto_list
    #
    # @staticmethod
    # def workflow_snapshot_meta_to_proto(workflow_snapshot_meta: WorkflowSnapshotMeta) -> WorkflowSnapshotProto:
    #     if workflow_snapshot_meta is None:
    #         return None
    #     else:
    #         return WorkflowSnapshotProto(workflow_id=int64Value(workflow_snapshot_meta.workflow_id),
    #                                      uri=stringValue(workflow_snapshot_meta.uri),
    #                                      signature=stringValue(workflow_snapshot_meta.signature),
    #                                      create_time=int64Value(workflow_snapshot_meta.create_time),
    #                                      uuid=workflow_snapshot_meta.uuid)
    #
    # @staticmethod
    # def workflow_snapshot_meta_list_to_proto(snapshots: List[WorkflowSnapshotMeta]) -> List[WorkflowSnapshotProto]:
    #     workflow_snapshot_list = []
    #     for workflow_snapshot in snapshots:
    #         workflow_snapshot_list.append(MetaToProto.workflow_snapshot_meta_to_proto(workflow_snapshot))
    #     return workflow_snapshot_list
    #
    # @staticmethod
    # def artifact_meta_to_proto(artifact_meta: ArtifactMeta) -> ArtifactProto:
    #     if artifact_meta is None:
    #         return None
    #     else:
    #         return ArtifactProto(
    #             uuid=artifact_meta.uuid,
    #             name=artifact_meta.name,
    #             properties=artifact_meta.properties,
    #             artifact_type=stringValue(artifact_meta.artifact_type),
    #             description=stringValue(artifact_meta.description),
    #             uri=stringValue(artifact_meta.uri),
    #             create_time=int64Value(artifact_meta.create_time),
    #             update_time=int64Value(artifact_meta.update_time))
    #
    # @staticmethod
    # def artifact_meta_list_to_proto(artifacts: List[ArtifactMeta]) -> List[ArtifactProto]:
    #     artifact_proto_list = []
    #     for artifact in artifacts:
    #         artifact_proto_list.append(MetaToProto.artifact_meta_to_proto(artifact))
    #     return artifact_proto_list

