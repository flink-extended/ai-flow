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
from sqlalchemy import Column, String, Integer, Binary, DateTime, Boolean, BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from ai_flow.common.util.time_utils import utcnow
from ai_flow.metadata.base import Base


class WorkflowMeta(Base):
    __tablename__ = 'workflow'

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(256))
    namespace = Column(String(256),
                       ForeignKey('namespace.name', ondelete='cascade'), nullable=False)
    workflow_object = Column(Binary, nullable=False)
    content = Column(String(length=1048576), nullable=False)
    create_time = Column(DateTime)
    update_time = Column(DateTime)
    enable = Column(Boolean, default=True)
    event_offset = Column(BigInteger, default=-1)

    namespace_meta = relationship('NamespaceMeta')
    __table_args__ = (
        UniqueConstraint('namespace', 'name'),
    )

    def __init__(self,
                 name: str,
                 namespace: str,
                 content: str,
                 workflow_object) -> None:
        self.name = name
        self.namespace = namespace
        self.content = content
        self.workflow_object = workflow_object
        self.create_time = utcnow()
        self.update_time = utcnow()
