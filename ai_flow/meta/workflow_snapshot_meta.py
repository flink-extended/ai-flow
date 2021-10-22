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
from ai_flow.util.json_utils import Jsonable
from typing import Text


class WorkflowSnapshotMeta(Jsonable):
    """define workflow snapshot meta"""

    def __init__(self,
                 workflow_id: int,
                 uri: Text,
                 signature: Text,
                 create_time: int = None,
                 uuid: int = None):
        self.workflow_id = workflow_id
        self.uri = uri
        self.signature = signature
        self.create_time = create_time
        self.uuid = uuid

    def __str__(self):
        return '<\n' \
               'WorkflowSnapshotMeta\n' \
               'uuid:{},\n' \
               'workflow_id:{},\n' \
               'uri:{},\n' \
               'signature:{},\n' \
               'create_time:{},\n' \
               '>'.format(self.uuid,
                          self.workflow_id,
                          self.uri,
                          self.signature,
                          self.create_time)
