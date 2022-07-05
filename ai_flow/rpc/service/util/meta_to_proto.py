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

from ai_flow.metadata.task_execution import TaskExecutionMeta
from ai_flow.metadata.workflow_event_trigger import WorkflowEventTriggerMeta
from ai_flow.metadata.workflow_schedule import WorkflowScheduleMeta
from ai_flow.metadata.workflow_execution import WorkflowExecutionMeta
from ai_flow.metadata.workflow_snapshot import WorkflowSnapshotMeta
from ai_flow.common.util.time_utils import datetime_to_timestamp
from ai_flow.metadata.workflow import WorkflowMeta
from ai_flow.metadata.namespace import NamespaceMeta
from ai_flow.rpc.protobuf.message_pb2 import NamespaceProto, WorkflowProto, WorkflowSnapshotProto, \
    WorkflowExecutionProto, WorkflowScheduleProto, WorkflowTriggerProto, TaskExecutionProto
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
                                 create_time=int64_value(datetime_to_timestamp(workflow.create_time)),
                                 update_time=int64_value(datetime_to_timestamp(workflow.update_time)),
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
                                         create_time=int64_value(datetime_to_timestamp(workflow_snapshot.create_time)),
                                         workflow_object=workflow_snapshot.workflow_object,
                                         uri=string_value(workflow_snapshot.uri),
                                         signature=string_value(workflow_snapshot.signature))

    @staticmethod
    def workflow_snapshot_meta_list_to_proto(workflow_snapshots: List[WorkflowSnapshotMeta]) -> List[WorkflowSnapshotProto]:
        workflow_snapshot_proto_list = []
        for snapshot in workflow_snapshots:
            workflow_snapshot_proto_list.append(MetaToProto.workflow_snapshot_meta_to_proto(snapshot))
        return workflow_snapshot_proto_list

    @staticmethod
    def workflow_execution_meta_to_proto(workflow_execution: WorkflowExecutionMeta) -> WorkflowExecutionProto:
        if workflow_execution is None:
            return None
        else:
            return WorkflowExecutionProto(uuid=workflow_execution.id,
                                          workflow_id=workflow_execution.workflow_id,
                                          begin_date=int64_value(datetime_to_timestamp(workflow_execution.begin_date)),
                                          end_date=int64_value(datetime_to_timestamp(workflow_execution.end_date)),
                                          status=string_value(workflow_execution.status),
                                          run_type=string_value(workflow_execution.run_type),
                                          snapshot_id=workflow_execution.snapshot_id,
                                          event_offset=int64_value(workflow_execution.event_offset))

    @staticmethod
    def workflow_execution_meta_list_to_proto(executions: List[WorkflowExecutionMeta]) -> List[WorkflowExecutionProto]:
        workflow_execution_proto_list = []
        for we in executions:
            workflow_execution_proto_list.append(MetaToProto.workflow_execution_meta_to_proto(we))
        return workflow_execution_proto_list

    @staticmethod
    def task_execution_meta_to_proto(task_execution: TaskExecutionMeta) -> TaskExecutionProto:
        if task_execution is None:
            return None
        else:
            return TaskExecutionProto(uuid=task_execution.id,
                                      workflow_execution_id=task_execution.workflow_execution_id,
                                      task_name=task_execution.task_name,
                                      sequence_number=task_execution.sequence_number,
                                      try_number=task_execution.try_number,
                                      begin_date=int64_value(datetime_to_timestamp(task_execution.begin_date)),
                                      end_date=int64_value(datetime_to_timestamp(task_execution.end_date)),
                                      status=string_value(task_execution.status))

    @staticmethod
    def task_execution_meta_list_to_proto(executions: List[TaskExecutionMeta]) -> List[TaskExecutionProto]:
        task_execution_proto_list = []
        for te in executions:
            task_execution_proto_list.append(MetaToProto.task_execution_meta_to_proto(te))
        return task_execution_proto_list

    @staticmethod
    def workflow_schedule_meta_to_proto(workflow_schedule: WorkflowScheduleMeta) -> WorkflowScheduleProto:
        if workflow_schedule is None:
            return None
        else:
            return WorkflowScheduleProto(uuid=workflow_schedule.id,
                                         workflow_id=workflow_schedule.workflow_id,
                                         expression=string_value(workflow_schedule.expression),
                                         is_paused=workflow_schedule.is_paused,
                                         create_time=int64_value(datetime_to_timestamp(workflow_schedule.create_time)))

    @staticmethod
    def workflow_schedule_meta_list_to_proto(workflow_schedules: List[WorkflowScheduleMeta]) -> List[WorkflowScheduleProto]:
        workflow_schedule_proto_list = []
        for ws in workflow_schedules:
            workflow_schedule_proto_list.append(MetaToProto.workflow_schedule_meta_to_proto(ws))
        return workflow_schedule_proto_list

    @staticmethod
    def workflow_trigger_meta_to_proto(workflow_trigger: WorkflowEventTriggerMeta) -> WorkflowTriggerProto:
        if workflow_trigger is None:
            return None
        else:
            return WorkflowTriggerProto(uuid=workflow_trigger.id,
                                        workflow_id=workflow_trigger.workflow_id,
                                        rule=workflow_trigger.rule,
                                        is_paused=workflow_trigger.is_paused,
                                        create_time=int64_value(datetime_to_timestamp(workflow_trigger.create_time)))

    @staticmethod
    def workflow_trigger_meta_list_to_proto(workflow_triggers: List[WorkflowEventTriggerMeta]) -> List[WorkflowTriggerProto]:
        workflow_trigger_proto_list = []
        for wt in workflow_triggers:
            workflow_trigger_proto_list.append(MetaToProto.workflow_trigger_meta_to_proto(wt))
        return workflow_trigger_proto_list

