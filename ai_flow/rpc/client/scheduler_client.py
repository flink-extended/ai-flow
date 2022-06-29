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
from ai_flow.metadata.workflow import WorkflowMeta

from ai_flow.rpc.client.util.response_unwrapper import unwrap_string_response, unwrap_workflow_list_response, \
    unwrap_bool_response, unwrap_workflow_response
from ai_flow.rpc.protobuf import scheduler_service_pb2_grpc
from ai_flow.rpc.protobuf.message_pb2 import WorkflowIdentifier, WorkflowProto
from ai_flow.rpc.protobuf.scheduler_service_pb2 import ListWorkflowsRequest, UpdateWorkflowRequest


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

    def update_workflow(self, name, namespace, content: str, pickled_workflow: bytes, is_enabled: bool) -> Optional[
        WorkflowMeta]:
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

    def start_workflow_execution(self, workflow_name, namespace):
        request = WorkflowIdentifier(namespace=namespace, workflow_name=workflow_name)
        self.scheduler_stub.startWorkflowExecution(request)

