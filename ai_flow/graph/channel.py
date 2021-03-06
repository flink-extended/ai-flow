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
from typing import Text, Optional
from ai_flow.util.json_utils import Jsonable


class Channel(Jsonable):
    """
    The output of the Nodes(ai_flow.graph.node.Node).
    """

    def __init__(self,
                 node_id: Text,
                 port: Optional[int] = 0) -> None:
        """
        :param node_id: node_id is the unique identifier of the node.
        :param port: the index of the node outputs
        """
        super().__init__()
        self.node_id = node_id
        self.port = port
