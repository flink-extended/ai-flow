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
from ai_flow.metadata.task_execution import TaskExecutionMeta

from ai_flow.metadata.workflow_event_trigger import WorkflowEventTriggerMeta

from ai_flow.metadata.workflow_schedule import WorkflowScheduleMeta

from ai_flow.metadata.workflow_execution import WorkflowExecutionMeta

from ai_flow.metadata.workflow import WorkflowMeta
from ai_flow.rpc import string_value

from ai_flow.rpc.client.util.response_unwrapper import unwrap_workflow_list_response, \
    unwrap_bool_response, unwrap_workflow_response, unwrap_workflow_execution_response, \
    unwrap_workflow_execution_list_response, unwrap_workflow_schedule_response, unwrap_workflow_schedule_list_response, \
    unwrap_workflow_trigger_response, unwrap_workflow_trigger_list_response, unwrap_task_execution_response, \
    unwrap_task_execution_list_response
from ai_flow.rpc.protobuf import scheduler_service_pb2_grpc
from ai_flow.rpc.protobuf.message_pb2 import WorkflowIdentifier, WorkflowProto, IdRequest, WorkflowScheduleProto, \
    WorkflowTriggerProto, TaskExecutionIdentifier
from ai_flow.rpc.protobuf.scheduler_service_pb2 import ListWorkflowsRequest, UpdateWorkflowRequest, \
    ListWorkflowItemsRequest, ListTaskExecutionsRequest


class SchedulerClient(object):
    def __init__(self, server_uri):
        channel = grpc.insecure_channel(server_uri)
        self.scheduler_stub = scheduler_service_pb2_grpc.SchedulerServiceStub(channel)

    def add_workflow(self, name, namespace, content: str, pickled_workflow: bytes) -> Optional[WorkflowMeta]:
        request = WorkflowProto(name=name, namespace=namespace, content=content, pickled_workflow=pickled_workflow)
        response = self.scheduler_stub.addWorkflow(request)
        return unwrap_workflow_response(response)

    def get_workflow(self, name, namespace) -> Optional[WorkflowMeta]:
        request = WorkflowIdentifier(namespace=namespace, workflow_name=name)
        response = self.scheduler_stub.getWorkflow(request)
        return unwrap_workflow_response(response)

    def update_workflow(self, name, namespace, content: str,
                        pickled_workflow: bytes, is_enabled: bool) -> Optional[WorkflowMeta]:
        workflow_identifier = WorkflowIdentifier(namespace=namespace, workflow_name=name)
        request = UpdateWorkflowRequest(identifier=workflow_identifier, content=content,
                                        pickled_workflow=pickled_workflow, is_enabled=is_enabled)
        response = self.scheduler_stub.updateWorkflow(request)
        return unwrap_workflow_response(response)

    def delete_workflow(self, name, namespace) -> bool:
        request = WorkflowIdentifier(namespace=namespace, workflow_name=name)
        response = self.scheduler_stub.deleteWorkflow(request)
        return unwrap_bool_response(response)

    def list_workflows(self, namespace, page_size=None, offset=None) -> Optional[List[WorkflowMeta]]:
        request = ListWorkflowsRequest(namespace=namespace,
                                       page_size=page_size,
                                       offset=offset)
        response = self.scheduler_stub.listWorkflows(request)
        return unwrap_workflow_list_response(response)

    def disable_workflow(self, name, namespace) -> bool:
        request = WorkflowIdentifier(namespace=namespace, workflow_name=name)
        response = self.scheduler_stub.disableWorkflow(request)
        return unwrap_bool_response(response)

    def enable_workflow(self, name, namespace) -> bool:
        request = WorkflowIdentifier(namespace=namespace, workflow_name=name)
        response = self.scheduler_stub.enableWorkflow(request)
        return unwrap_bool_response(response)

    def start_workflow_execution(self, workflow_name, namespace) -> bool:
        request = WorkflowIdentifier(namespace=namespace, workflow_name=workflow_name)
        response = self.scheduler_stub.startWorkflowExecution(request)
        return unwrap_bool_response(response)

    def stop_workflow_execution(self, workflow_execution_id) -> bool:
        request = IdRequest(id=workflow_execution_id)
        response = self.scheduler_stub.stopWorkflowExecution(request)
        return unwrap_bool_response(response)

    def stop_workflow_executions(self, namespace, workflow_name) -> bool:
        request = WorkflowIdentifier(namespace=namespace, workflow_name=workflow_name)
        response = self.scheduler_stub.stopWorkflowExecutions(request)
        return unwrap_bool_response(response)

    def get_workflow_execution(self, workflow_execution_id) -> Optional[WorkflowExecutionMeta]:
        request = IdRequest(id=workflow_execution_id)
        response = self.scheduler_stub.getWorkflowExecution(request)
        return unwrap_workflow_execution_response(response)

    def list_workflow_executions(self, namespace, workflow_name, page_size=None,
                                 offset=None) -> Optional[List[WorkflowExecutionMeta]]:
        request = ListWorkflowItemsRequest(namespace=namespace, workflow_name=workflow_name,
                                           page_size=page_size, offset=offset)
        response = self.scheduler_stub.listWorkflowExecutions(request)
        return unwrap_workflow_execution_list_response(response)

    def start_task_execution(self, workflow_execution_id, task_name) -> bool:
        request = TaskExecutionIdentifier(workflow_execution_id=workflow_execution_id,
                                          task_name=task_name)
        response = self.scheduler_stub.startTaskExecution(request)
        return unwrap_bool_response(response)

    def stop_task_execution(self, workflow_execution_id, task_name) -> bool:
        request = TaskExecutionIdentifier(workflow_execution_id=workflow_execution_id,
                                          task_name=task_name)
        response = self.scheduler_stub.stopTaskExecution(request)
        return unwrap_bool_response(response)

    def get_task_execution(self, task_execution_id) -> Optional[TaskExecutionMeta]:
        request = IdRequest(id=task_execution_id)
        response = self.scheduler_stub.getTaskExecution(request)
        return unwrap_task_execution_response(response)

    def list_task_executions(self, workflow_execution_id, page_size=None,
                             offset=None) -> Optional[List[TaskExecutionMeta]]:
        request = ListTaskExecutionsRequest(workflow_execution_id=workflow_execution_id,
                                            page_size=page_size,
                                            offset=offset)
        response = self.scheduler_stub.listTaskExecutions(request)
        return unwrap_task_execution_list_response(response)

    def add_workflow_schedule(self, namespace, workflow_name, expression) -> Optional[WorkflowScheduleMeta]:
        workflow = self.get_workflow(name=workflow_name, namespace=namespace)
        request = WorkflowScheduleProto(workflow_id=workflow.id,
                                        expression=string_value(expression))
        response = self.scheduler_stub.addWorkflowSchedule(request)
        return unwrap_workflow_schedule_response(response)

    def get_workflow_schedule(self, schedule_id) -> Optional[WorkflowScheduleMeta]:
        request = IdRequest(id=schedule_id)
        response = self.scheduler_stub.getWorkflowSchedule(request)
        return unwrap_workflow_schedule_response(response)

    def list_workflow_schedules(self, namespace, workflow_name, page_size=None, offset=None) -> Optional[List[WorkflowScheduleMeta]]:
        request = ListWorkflowItemsRequest(namespace=namespace, workflow_name=workflow_name,
                                           page_size=page_size, offset=offset)
        response = self.scheduler_stub.listWorkflowSchedules(request)
        return unwrap_workflow_schedule_list_response(response)

    def delete_workflow_schedule(self, schedule_id) -> bool:
        request = IdRequest(id=schedule_id)
        response = self.scheduler_stub.deleteWorkflowSchedule(request)
        return unwrap_bool_response(response)

    def delete_workflow_schedules(self, namespace, workflow_name) -> bool:
        request = WorkflowIdentifier(namespace=namespace, workflow_name=workflow_name)
        response = self.scheduler_stub.deleteWorkflowSchedules(request)
        return unwrap_bool_response(response)

    def pause_workflow_schedule(self, schedule_id) -> bool:
        request = IdRequest(id=schedule_id)
        response = self.scheduler_stub.pauseWorkflowSchedule(request)
        return unwrap_bool_response(response)

    def resume_workflow_schedule(self, schedule_id) -> bool:
        request = IdRequest(id=schedule_id)
        response = self.scheduler_stub.resumeWorkflowSchedule(request)
        return unwrap_bool_response(response)

    def add_workflow_trigger(self, namespace, workflow_name, rule: bytes) -> Optional[WorkflowEventTriggerMeta]:
        workflow = self.get_workflow(name=workflow_name, namespace=namespace)
        request = WorkflowTriggerProto(workflow_id=workflow.id,
                                       rule=rule)
        response = self.scheduler_stub.addWorkflowTrigger(request)
        return unwrap_workflow_trigger_response(response)

    def get_workflow_trigger(self, trigger_id) -> Optional[WorkflowEventTriggerMeta]:
        request = IdRequest(id=trigger_id)
        response = self.scheduler_stub.getWorkflowTrigger(request)
        return unwrap_workflow_trigger_response(response)

    def list_workflow_triggers(self, namespace, workflow_name, page_size=None, offset=None
                               ) -> Optional[List[WorkflowEventTriggerMeta]]:
        request = ListWorkflowItemsRequest(namespace=namespace, workflow_name=workflow_name,
                                           page_size=page_size, offset=offset)
        response = self.scheduler_stub.listWorkflowTriggers(request)
        return unwrap_workflow_trigger_list_response(response)

    def delete_workflow_trigger(self, trigger_id) -> bool:
        request = IdRequest(id=trigger_id)
        response = self.scheduler_stub.deleteWorkflowTrigger(request)
        return unwrap_bool_response(response)

    def delete_workflow_triggers(self, namespace, workflow_name) -> bool:
        request = WorkflowIdentifier(namespace=namespace, workflow_name=workflow_name)
        response = self.scheduler_stub.deleteWorkflowTriggers(request)
        return unwrap_bool_response(response)

    def pause_workflow_trigger(self, trigger_id) -> bool:
        request = IdRequest(id=trigger_id)
        response = self.scheduler_stub.pauseWorkflowTrigger(request)
        return unwrap_bool_response(response)

    def resume_workflow_trigger(self, trigger_id) -> bool:
        request = IdRequest(id=trigger_id)
        response = self.scheduler_stub.resumeWorkflowTrigger(request)
        return unwrap_bool_response(response)



