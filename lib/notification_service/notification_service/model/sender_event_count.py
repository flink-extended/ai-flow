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


class SenderEventCount(object):
    def __init__(self, sender: str, event_count: int):
        self.sender = sender
        self.event_count = event_count

    def __str__(self) -> str:
        return 'sender:{0}, event_count:{1}'.format(self.sender, self.event_count)

    def __eq__(self, other):
        if not isinstance(other, SenderEventCount):
            return False
        return self.sender == other.sender and self.event_count == other.event_count
