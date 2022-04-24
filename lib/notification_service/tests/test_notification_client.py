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
import unittest

from notification_service.notification_client import get_notification_client
from tests.mock_classes import MockNotificationClient


class TestNotificationClient(unittest.TestCase):
    def test_get_notification_client(self):
        client = get_notification_client(class_name='tests.mock_classes.MockNotificationClient',
                                         namespace='default',
                                         sender='sender')
        self.assertTrue(isinstance(client, MockNotificationClient))


if __name__ == '__main__':
    unittest.main()
