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
import grpc

from ai_flow.rpc.protobuf import heartbeat_service_pb2_grpc
from ai_flow.rpc.protobuf.heartbeat_service_pb2 import HeartbeatRequest


class HeartbeatClient(object):
    def __init__(self, server_uri):
        channel = grpc.insecure_channel(server_uri)
        self.stub = heartbeat_service_pb2_grpc.HeartbeatServiceStub(channel)

    def send_heartbeat(self, workflow_execution_id, task_name, seq_num):
        request = HeartbeatRequest(workflow_execution_id=workflow_execution_id,
                                   task_name=task_name,
                                   sequence_number=seq_num)
        response = self.stub.send_heartbeat(request)
        return response.return_code
