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
import unittest
import datetime

import pendulum

from ai_flow.common.util import time_utils


class TestTimeUtils(unittest.TestCase):

    def test_date_parse(self):
        time = datetime.datetime(2022, 1, 1, 1, 1, 1)
        epoch = time_utils.datetime_to_timestamp(time)
        print(epoch)
        new_time = time_utils.timestamp_to_datetime(epoch)
        print(new_time)
        self.assertEqual(time, new_time)

    def test_utc_date_parse(self):
        time = datetime.datetime(2022, 1, 1, 1, 1, 1, tzinfo=pendulum.tz.timezone('UTC'))
        epoch = time_utils.datetime_to_utc_timestamp(time)
        print(epoch)
        new_time = time_utils.utc_timestamp_to_datetime(epoch)
        print(new_time)
        self.assertEqual(time, new_time)
