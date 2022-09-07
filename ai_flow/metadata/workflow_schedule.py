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

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ai_flow.metadata.base import Base


class WorkflowScheduleMeta(Base):
    """
    It represents the metadata of the WorkflowSchedule.
    :param id: The unique identify of the WorkflowSchedule.
    :param workflow_id: The unique identify of the Workflow.
    :param expression: The expression for periodic scheduling Workflow.
    :param create_time: The create time of the WorkflowSchedule.
    :param is_paused: Whether to suspend scheduling.
    """
    __tablename__ = 'workflow_schedule'

    id = Column(Integer, autoincrement=True, primary_key=True)
    workflow_id = Column(Integer, ForeignKey('workflow.id'))
    expression = Column(String(256))
    create_time = Column(DateTime)
    is_paused = Column(Boolean, default=False)

    workflow = relationship('WorkflowMeta')

    def __init__(self,
                 workflow_id,
                 expression,
                 is_paused=False,
                 create_time=None,
                 uuid=None):
        self.workflow_id = workflow_id
        self.expression = expression
        self.is_paused = is_paused
        self.create_time = datetime.now() if create_time is None else create_time
        self.id = uuid
