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
import grpc

from ai_flow.model.task_execution import TaskExecutionKey
from ai_flow.rpc.protobuf import heartbeat_service_pb2_grpc
from ai_flow.rpc.protobuf.heartbeat_service_pb2 import HeartbeatRequest


class HeartbeatClient(object):
    def __init__(self, server_uri):
        channel = grpc.insecure_channel(server_uri)
        self.stub = heartbeat_service_pb2_grpc.HeartbeatServiceStub(channel)

    def send_heartbeat(self, key: TaskExecutionKey):
        request = HeartbeatRequest(workflow_execution_id=key.workflow_execution_id,
                                   task_name=key.task_name,
                                   sequence_number=key.seq_num)
        response = self.stub.send_heartbeat(request)
        return response.return_code
