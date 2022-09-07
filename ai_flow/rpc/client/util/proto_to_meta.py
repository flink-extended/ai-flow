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

from ai_flow.metadata.task_execution import TaskExecutionMeta
from ai_flow.metadata.workflow_event_trigger import WorkflowEventTriggerMeta
from ai_flow.metadata.workflow_schedule import WorkflowScheduleMeta
from ai_flow.metadata.workflow_execution import WorkflowExecutionMeta
from ai_flow.metadata.workflow_snapshot import WorkflowSnapshotMeta
from ai_flow.common.util.time_utils import timestamp_to_datetime
from ai_flow.metadata.workflow import WorkflowMeta
from ai_flow.metadata.namespace import NamespaceMeta
from ai_flow.rpc.protobuf.message_pb2 import NamespaceProto, WorkflowProto, WorkflowSnapshotProto, \
    WorkflowExecutionProto, WorkflowScheduleProto, WorkflowTriggerProto, TaskExecutionProto


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
                            create_time=timestamp_to_datetime(create_time_epoch),
                            update_time=timestamp_to_datetime(update_time_epoch),
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
    def proto_to_workflow_snapshot_meta(workflow_snapshot_proto: WorkflowSnapshotProto
                                        ) -> WorkflowSnapshotMeta:
        create_time_epoch = workflow_snapshot_proto.create_time.value \
            if workflow_snapshot_proto.HasField('create_time') else None
        uri = workflow_snapshot_proto.uri.value if workflow_snapshot_proto.HasField('uri') else None
        signature = workflow_snapshot_proto.signature.value if workflow_snapshot_proto.HasField('signature') else None
        return WorkflowSnapshotMeta(workflow_id=workflow_snapshot_proto.workflow_id,
                                    workflow_object=workflow_snapshot_proto.workflow_object,
                                    uri=uri,
                                    signature=signature,
                                    create_time=timestamp_to_datetime(create_time_epoch),
                                    uuid=workflow_snapshot_proto.uuid)

    @staticmethod
    def proto_to_workflow_snapshot_meta_list(
            snapshot_list_proto: List[WorkflowSnapshotProto]) -> List[WorkflowSnapshotMeta]:
        snapshot_list = []
        for snapshot_proto in snapshot_list_proto:
            snapshot_list.append(ProtoToMeta.proto_to_workflow_snapshot_meta(snapshot_proto))
        return snapshot_list

    @staticmethod
    def proto_to_workflow_execution_meta(proto: WorkflowExecutionProto) -> WorkflowExecutionMeta:
        run_type = proto.run_type.value if proto.HasField('run_type') else None
        begin_date_epoch = proto.begin_date.value if proto.HasField('begin_date') else None
        end_date_epoch = proto.end_date.value if proto.HasField('end_date') else None
        status = proto.status.value if proto.HasField('status') else None
        event_offset = proto.event_offset.value if proto.HasField('event_offset') else None
        return WorkflowExecutionMeta(workflow_id=proto.workflow_id,
                                     run_type=run_type,
                                     snapshot_id=proto.snapshot_id,
                                     begin_date=timestamp_to_datetime(begin_date_epoch),
                                     end_date=timestamp_to_datetime(end_date_epoch),
                                     status=status,
                                     event_offset=event_offset,
                                     uuid=proto.uuid)

    @staticmethod
    def proto_to_workflow_execution_meta_list(execution_list_proto: List[WorkflowExecutionProto]
                                              ) -> List[WorkflowExecutionMeta]:
        workflow_execution_list = []
        for proto in execution_list_proto:
            workflow_execution_list.append(ProtoToMeta.proto_to_workflow_execution_meta(proto))
        return workflow_execution_list

    @staticmethod
    def proto_to_task_execution_meta(proto: TaskExecutionProto) -> TaskExecutionMeta:
        begin_date_epoch = proto.begin_date.value if proto.HasField('begin_date') else None
        end_date_epoch = proto.end_date.value if proto.HasField('end_date') else None
        status = proto.status.value if proto.HasField('status') else None
        return TaskExecutionMeta(workflow_execution_id=proto.workflow_execution_id,
                                 task_name=proto.task_name,
                                 sequence_number=proto.sequence_number,
                                 try_number=proto.try_number,
                                 begin_date=timestamp_to_datetime(begin_date_epoch),
                                 end_date=timestamp_to_datetime(end_date_epoch),
                                 status=status,
                                 uuid=proto.uuid)

    @staticmethod
    def proto_to_task_execution_meta_list(execution_list_proto: List[TaskExecutionProto]) -> List[TaskExecutionMeta]:
        task_execution_list = []
        for proto in execution_list_proto:
            task_execution_list.append(ProtoToMeta.proto_to_task_execution_meta(proto))
        return task_execution_list

    @staticmethod
    def proto_to_workflow_schedule_meta(proto: WorkflowScheduleProto) -> WorkflowScheduleMeta:
        expression = proto.expression.value if proto.HasField('expression') else None
        create_time_epoch = proto.create_time.value if proto.HasField('create_time') else None
        return WorkflowScheduleMeta(workflow_id=proto.workflow_id,
                                    expression=expression,
                                    is_paused=proto.is_paused,
                                    create_time=timestamp_to_datetime(create_time_epoch),
                                    uuid=proto.uuid)

    @staticmethod
    def proto_to_workflow_schedule_meta_list(schedule_list_proto: List[WorkflowScheduleProto]
                                             ) -> List[WorkflowScheduleMeta]:
        workflow_schedule_list = []
        for proto in schedule_list_proto:
            workflow_schedule_list.append(ProtoToMeta.proto_to_workflow_schedule_meta(proto))
        return workflow_schedule_list

    @staticmethod
    def proto_to_workflow_trigger_meta(proto: WorkflowTriggerProto) -> WorkflowEventTriggerMeta:
        create_time_epoch = proto.create_time.value if proto.HasField('create_time') else None
        return WorkflowEventTriggerMeta(workflow_id=proto.workflow_id,
                                        rule=proto.rule,
                                        is_paused=proto.is_paused,
                                        create_time=timestamp_to_datetime(create_time_epoch),
                                        uuid=proto.uuid)

    @staticmethod
    def proto_to_workflow_trigger_meta_list(trigger_list_proto: List[WorkflowEventTriggerMeta]
                                            ) -> List[WorkflowTriggerProto]:
        workflow_trigger_list = []
        for proto in trigger_list_proto:
            workflow_trigger_list.append(ProtoToMeta.proto_to_workflow_trigger_meta(proto))
        return workflow_trigger_list


