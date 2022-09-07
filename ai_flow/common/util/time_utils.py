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
import time
import datetime
from calendar import timegm

from pytz import utc


def generate_local_time_str():
    return time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime())


def parse_date(timestamp):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(timestamp) / 1000))


def datetime_to_timestamp(d: datetime.datetime):
    if d is None:
        return 0
    else:
        return int(d.timestamp()*1000)


def timestamp_to_datetime(timestamp):
    return datetime.datetime.fromtimestamp(timestamp / 1000)


def datetime_to_utc_timestamp(timeval: datetime.datetime):
    """
    Converts a datetime instance to a timestamp.

    :type timeval: datetime
    :rtype: float

    """
    if timeval is not None:
        return timegm(timeval.utctimetuple()) + timeval.microsecond / 1000000


def utc_timestamp_to_datetime(timestamp):
    """
    Converts the given timestamp to a datetime instance.

    :type timestamp: float
    :rtype: datetime

    """
    if timestamp is not None:
        return datetime.datetime.fromtimestamp(timestamp, utc)

