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
import queue


class MessageQueue(object):

    def __init__(self) -> None:
        self.queue = queue.Queue()

    def send(self, event):
        self.queue.put_nowait(event)

    def get(self):
        return self.queue.get()

    def length(self):
        return self.queue.qsize()

    def get_with_timeout(self, timeout=1):
        try:
            return self.queue.get(timeout=timeout)
        except Exception as e:
            return None
