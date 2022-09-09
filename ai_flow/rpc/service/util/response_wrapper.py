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
import traceback
from functools import wraps
from typing import List

from google.protobuf.json_format import MessageToJson

from ai_flow.common.result import BaseResult, RetCode
from ai_flow.rpc.protobuf.message_pb2 import Response, SUCCESS, ReturnCode, RESOURCE_DOES_NOT_EXIST, NamespaceProto, \
    INTERNAL_ERROR, WorkflowProto, WorkflowSnapshotProto, WorkflowExecutionProto, WorkflowScheduleProto, \
    WorkflowTriggerProto, TaskExecutionProto
from ai_flow.rpc.protobuf.scheduler_service_pb2 import WorkflowListProto, WorkflowExecutionListProto, \
    WorkflowScheduleListProto, WorkflowTriggerListProto, TaskExecutionListProto, WorkflowSnapshotListProto, \
    NamespaceListProto
from ai_flow.rpc.server.exceptions import AIFlowRpcServerException


def catch_exception(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AIFlowRpcServerException as e:
            return Response(return_code=str(e.error_code), error_msg=traceback.format_exc())
        except Exception as ex:
            return Response(return_code=str(INTERNAL_ERROR), error_msg=traceback.format_exc())

    return wrapper


def wrap_data_response(data):
    if data is not None:
        return Response(return_code=str(SUCCESS), error_msg=None,
                        data=MessageToJson(data, preserving_proto_field_name=True))
    else:
        return Response(return_code=str(RESOURCE_DOES_NOT_EXIST),
                        error_msg=ReturnCode.Name(RESOURCE_DOES_NOT_EXIST).lower(),
                        data=None)


def wrap_result_response(result: BaseResult):
    if result.status == RetCode.OK:
        return Response(return_code=str(SUCCESS), error_msg=None, data=result.message)
    else:
        return Response(return_code=str(INTERNAL_ERROR), error_msg=result.message,
                        data=None)


def wrap_namespace_list_response(namespace_list: List[NamespaceProto]):
    if namespace_list is None or len(namespace_list) == 0:
        return Response(return_code=str(RESOURCE_DOES_NOT_EXIST),
                        error_msg=ReturnCode.Name(RESOURCE_DOES_NOT_EXIST).lower(),
                        data=None)
    else:
        list_proto = NamespaceListProto(namespaces=namespace_list)
        return Response(return_code=str(SUCCESS),
                        error_msg=None,
                        data=MessageToJson(list_proto, preserving_proto_field_name=True))


def wrap_workflow_list_response(workflow_list: List[WorkflowProto]):
    if workflow_list is None or len(workflow_list) == 0:
        return Response(return_code=str(RESOURCE_DOES_NOT_EXIST),
                        error_msg=ReturnCode.Name(RESOURCE_DOES_NOT_EXIST).lower(),
                        data=None)
    else:
        list_proto = WorkflowListProto(workflows=workflow_list)
        return Response(return_code=str(SUCCESS),
                        error_msg=None,
                        data=MessageToJson(list_proto, preserving_proto_field_name=True))


def wrap_workflow_snapshot_list_response(workflow_snapshot_list: List[WorkflowSnapshotProto]):
    if workflow_snapshot_list is None or len(workflow_snapshot_list) == 0:
        return Response(return_code=str(RESOURCE_DOES_NOT_EXIST),
                        error_msg=ReturnCode.Name(RESOURCE_DOES_NOT_EXIST).lower(),
                        data=None)
    else:
        list_proto = WorkflowSnapshotListProto(workflow_snapshots=workflow_snapshot_list)
        return Response(return_code=str(SUCCESS),
                        error_msg=None,
                        data=MessageToJson(list_proto, preserving_proto_field_name=True))


def wrap_workflow_execution_list_response(workflow_execution_list: List[WorkflowExecutionProto]):
    if workflow_execution_list is None or len(workflow_execution_list) == 0:
        return Response(return_code=str(RESOURCE_DOES_NOT_EXIST),
                        error_msg=ReturnCode.Name(RESOURCE_DOES_NOT_EXIST).lower(),
                        data=None)
    else:
        list_proto = WorkflowExecutionListProto(workflow_executions=workflow_execution_list)
        return Response(return_code=str(SUCCESS),
                        error_msg=None,
                        data=MessageToJson(list_proto, preserving_proto_field_name=True))


def wrap_task_execution_list_response(task_execution_list: List[TaskExecutionProto]):
    if task_execution_list is None or len(task_execution_list) == 0:
        return Response(return_code=str(RESOURCE_DOES_NOT_EXIST),
                        error_msg=ReturnCode.Name(RESOURCE_DOES_NOT_EXIST).lower(),
                        data=None)
    else:
        list_proto = TaskExecutionListProto(task_executions=task_execution_list)
        return Response(return_code=str(SUCCESS),
                        error_msg=None,
                        data=MessageToJson(list_proto, preserving_proto_field_name=True))


def wrap_workflow_schedule_list_response(workflow_schedule_list: List[WorkflowScheduleProto]):
    if workflow_schedule_list is None or len(workflow_schedule_list) == 0:
        return Response(return_code=str(RESOURCE_DOES_NOT_EXIST),
                        error_msg=ReturnCode.Name(RESOURCE_DOES_NOT_EXIST).lower(),
                        data=None)
    else:
        list_proto = WorkflowScheduleListProto(workflow_schedules=workflow_schedule_list)
        return Response(return_code=str(SUCCESS),
                        error_msg=None,
                        data=MessageToJson(list_proto, preserving_proto_field_name=True))


def wrap_workflow_trigger_list_response(workflow_trigger_list: List[WorkflowTriggerProto]):
    if workflow_trigger_list is None or len(workflow_trigger_list) == 0:
        return Response(return_code=str(RESOURCE_DOES_NOT_EXIST),
                        error_msg=ReturnCode.Name(RESOURCE_DOES_NOT_EXIST).lower(),
                        data=None)
    else:
        list_proto = WorkflowTriggerListProto(workflow_triggers=workflow_trigger_list)
        return Response(return_code=str(SUCCESS),
                        error_msg=None,
                        data=MessageToJson(list_proto, preserving_proto_field_name=True))
