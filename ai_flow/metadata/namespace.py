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
import json
from sqlalchemy import Column, String

from ai_flow.metadata.base import Base


class NamespaceMeta(Base):
    """
    It represents the metadata of the Namespace.
    :param name: The name of the Namespace.
    :param properties: The properties of the Namespace.
    """

    __tablename__ = 'namespace'

    name = Column(String(256), primary_key=True, nullable=False, unique=True)
    properties = Column(String(1024))

    def __init__(self,
                 name: str,
                 properties: dict) -> None:
        self.name = name
        self.properties = json.dumps(properties)

    def get_properties(self) -> dict:
        if self.properties is None:
            return None
        return json.loads(self.properties)

    def set_properties(self, value):
        self.properties = json.dumps(value)
