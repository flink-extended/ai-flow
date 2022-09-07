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
import logging

from ai_flow.common.configuration import config_constants
from ai_flow.rpc.server.server import AIFlowServer


class AIFlowServerRunner(object):
    """
    This class is the runner class for the AIFlowServer. It meant to manage the lifecycle of the AIFlowServer
    and high availability in the future.
    """

    def __init__(self) -> None:
        self.server: AIFlowServer = None

    def start(self, is_block=False) -> None:
        """
        Start the AIFlow server.

        :param is_block: AI flow runner will run non-stop if True.
        """
        self.server = AIFlowServer()
        self.server.run(is_block=is_block)
        if not is_block:
            self._wait_for_server_available(timeout=config_constants.SERVER_START_TIMEOUT)

    def stop(self) -> None:
        """
        Stop the AIFlow server.
        """
        self.server.stop()

    @staticmethod
    def _wait_for_server_available(timeout):
        """
        Wait for server to be started and available.

        :param timeout: Float value. Seconds to wait for server available.
                        If None, wait forever until server started.
        """
        server_uri = 'localhost:{}'.format(config_constants.RPC_PORT)
        try:
            channel = grpc.insecure_channel(server_uri)
            grpc.channel_ready_future(channel).result(timeout=timeout)
            logging.info("AIFlow Server started successfully.")
        except grpc.FutureTimeoutError as e:
            logging.error('AIFlow Server is not available after waiting for {} seconds.'.format(timeout))
            raise e
