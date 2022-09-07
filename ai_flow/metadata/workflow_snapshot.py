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

from sqlalchemy import Column, String, Integer, Binary, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ai_flow.metadata.base import Base


class WorkflowSnapshotMeta(Base):
    """
    It represents the metadata of the WorkflowSnapshot.
    :param id: The unique identify of the WorkflowSnapshot.
    :param workflow_id: The unique identify of the Workflow.
    :param create_time: The create time of the WorkflowSnapshot.
    :param workflow_object: The Workflow serialized object.
    :param uri: The address where the Workflow snapshot is stored.
    :param signature: The signature of the WorkflowSnapshot.
    """
    __tablename__ = 'workflow_snapshot'

    id = Column(Integer, autoincrement=True, primary_key=True)
    workflow_id = Column(Integer, ForeignKey('workflow.id'))
    create_time = Column(DateTime)
    workflow_object = Column(Binary)
    uri = Column(String(1024))
    signature = Column(String(256))

    workflow = relationship('WorkflowMeta')

    def __init__(self,
                 workflow_id,
                 workflow_object,
                 uri,
                 signature,
                 create_time=None,
                 uuid=None):
        self.workflow_id = workflow_id
        self.workflow_object = workflow_object
        self.uri = uri
        self.signature = signature
        self.create_time = datetime.now() if create_time is None else create_time
        self.id = uuid
