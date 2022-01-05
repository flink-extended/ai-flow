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
import unittest
import os
from ai_flow.endpoint.server.server_runner import AIFlowServerRunner
from ai_flow.test.util.notification_service_utils import start_notification_server, stop_notification_server


class TestServerRunner(unittest.TestCase):
    def setUp(self) -> None:
        self.ns_server = start_notification_server()

    def tearDown(self) -> None:
        stop_notification_server(self.ns_server)

    def test_server_start_stop(self):
        server_runner = AIFlowServerRunner(config_file=os.path.dirname(__file__) + '/aiflow_server.yaml')
        server_runner.start(is_block=False)
        server_runner.stop()

    def test__wait_for_server_available(self):
        from grpc import FutureTimeoutError
        server_runner = AIFlowServerRunner(config_file=os.path.dirname(__file__) + '/aiflow_server.yaml')

        server_runner.server_config.set_wait_for_server_started_timeout(0)
        with self.assertRaises(FutureTimeoutError):
            server_runner.start()
        server_runner.stop()

        server_runner.server_config.set_wait_for_server_started_timeout(5)
        server_runner.start()
        server_runner._wait_for_server_available(timeout=0.1)
        server_runner.stop()


if __name__ == '__main__':
    unittest.main()
