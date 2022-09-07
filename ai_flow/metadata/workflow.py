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
from datetime import datetime

from sqlalchemy import Column, String, Integer, Binary, DateTime, Boolean, BigInteger, ForeignKey, UniqueConstraint, \
    Text
from sqlalchemy.orm import relationship
from ai_flow.metadata.base import Base


class WorkflowMeta(Base):
    """
    It represents the metadata of the Workflow.
    :param id: The unique identify of the Workflow.
    :param name: The name of the Workflow.
    :param namespace: The namespace of the Workflow.
    :param workflow_object: The Workflow serialized object.
    :param content: The source code of the Workflow.
    :param create_time: The create time of the Workflow.
    :param update_time: The update time of the Workflow.
    :param enable: The properties of the Workflow.
    :param event_offset: Event processing progress corresponding to Workflow.
    """
    __tablename__ = 'workflow'

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(256))
    namespace = Column(String(256),
                       ForeignKey('namespace.name', ondelete='cascade'), nullable=False)
    workflow_object = Column(Binary, nullable=False)
    content = Column(Text, nullable=False)
    create_time = Column(DateTime)
    update_time = Column(DateTime)
    is_enabled = Column(Boolean, default=True)
    event_offset = Column(BigInteger, default=-1)

    namespace_meta = relationship('NamespaceMeta')
    __table_args__ = (
        UniqueConstraint('namespace', 'name'),
    )

    def __init__(self,
                 name: str,
                 namespace: str,
                 content: str,
                 workflow_object: bytes,
                 create_time=None,
                 update_time=None,
                 is_enabled=True,
                 event_offset=-1,
                 uuid=None) -> None:
        current_dt = datetime.now()
        self.name = name
        self.namespace = namespace
        self.content = content
        self.workflow_object = workflow_object
        self.create_time = current_dt if create_time is None else create_time
        self.update_time = current_dt if update_time is None else update_time
        self.is_enabled = is_enabled
        self.event_offset = event_offset
        self.id = uuid
