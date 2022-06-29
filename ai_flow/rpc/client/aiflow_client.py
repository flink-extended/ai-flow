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
from ai_flow.rpc.client.scheduler_client import SchedulerClient

from ai_flow.rpc.client.metadata_client import MetadataClient
from ai_flow.common.configuration import config_constants


class AIFlowClient(MetadataClient, SchedulerClient):
    def __init__(self, server_uri):
        self.server_uri = server_uri
        MetadataClient.__init__(self, server_uri)
        SchedulerClient.__init__(self, server_uri)
        self.wait_for_server_ready(60)   # TODO make it configurable

    def wait_for_server_ready(self, timeout):
        channel = grpc.insecure_channel(self.server_uri)
        fut = grpc.channel_ready_future(channel)
        fut.result(timeout)


def get_ai_flow_client():
    server_uri = config_constants.SERVER_ADDRESS
    return AIFlowClient(server_uri=server_uri)
