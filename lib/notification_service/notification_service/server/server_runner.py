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
import logging
import os

import grpc
from notification_service.server.ha_manager import SimpleNotificationServerHaManager
from notification_service.server.server import NotificationServer

from notification_service.storage.alchemy.db_event_storage import DbEventStorage
from notification_service.storage.alchemy.db_high_availability_storage import DbHighAvailabilityStorage
from notification_service.util.server_config import NotificationServerConfig
from notification_service.rpc.service import NotificationService, HighAvailableNotificationService
from notification_service.util.utils import get_ip_addr


logger = logging.getLogger(__name__)


class NotificationServerRunner(object):
    def __init__(self, config_file):
        if not os.path.exists(config_file):
            raise IOError('Config file {} not exist!'.format(config_file))
        logger.info("Loading Notification server config from path: {}".format(config_file))
        self.config = NotificationServerConfig(config_file=config_file)

    def _init_server(self):
        if self.config.db_uri:
            self.storage = DbEventStorage(self.config.db_uri)
        else:
            raise Exception('Failed to start notification service without database connection info.')
        if self.config.enable_ha:
            server_uri = self.config.advertised_uri \
                if self.config.advertised_uri is not None else get_ip_addr() + ':' + str(self.config.port)
            ha_storage = DbHighAvailabilityStorage(db_conn=self.config.db_uri)
            ha_manager = SimpleNotificationServerHaManager()
            service = HighAvailableNotificationService(
                self.storage,
                ha_manager,
                server_uri,
                ha_storage,
                5000)
            self.server = NotificationServer(service=service,
                                             port=int(self.config.port))
        else:
            self.server = NotificationServer(service=NotificationService(self.storage),
                                             port=int(self.config.port))

    def start(self, is_block=False):
        logger.info("Starting notification server with config: {}".format(self.config))
        self._init_server()
        self.server.run(is_block)
        if not is_block:
            self._wait_for_server_available(timeout=self.config.wait_for_server_started_timeout)

    def stop(self):
        self.server.stop()

    def _wait_for_server_available(self, timeout):
        """
        Wait for server to be started and available.

        :param timeout: Float value. Seconds to wait for server available.
                        If None, wait forever until server started.
        """
        server_uri = 'localhost:{}'.format(self.config.port)
        try:
            channel = grpc.insecure_channel(server_uri)
            grpc.channel_ready_future(channel).result(timeout=timeout)
            logging.info("Notification Server started successfully.")
        except grpc.FutureTimeoutError as e:
            logging.error('Notification Server is not available after waiting for {} seconds.'.format(timeout))
            raise e
