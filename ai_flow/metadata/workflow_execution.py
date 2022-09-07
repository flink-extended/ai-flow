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

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship

from ai_flow.metadata.base import Base
from ai_flow.model.status import WorkflowStatus


class WorkflowExecutionMeta(Base):
    """
    It represents the metadata of the WorkflowExecution.
    :param id: The unique identify of the WorkflowExecution.
    :param workflow_id: The unique identify of the Workflow.
    :param begin_date: The begin time of the WorkflowExecution.
    :param end_date: The end time of the WorkflowExecution.
    :param status: The status(Type:WorkflowStatus) of the WorkflowExecution.
    :param run_type: The run type(Type:ExecutionType) of the WorkflowExecution.
    :param snapshot_id: The unique identify of the WorkflowSnapshot.
    :param event_offset: Event processing progress corresponding to WorkflowExecution.
    """

    __tablename__ = 'workflow_execution'

    id = Column(Integer, autoincrement=True, primary_key=True)
    workflow_id = Column(Integer, ForeignKey('workflow.id'))
    begin_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(String(256))
    run_type = Column(String(256))
    snapshot_id = Column(Integer, ForeignKey('workflow_snapshot.id'))
    event_offset = Column(BigInteger, default=-1)

    workflow = relationship('WorkflowMeta')
    workflow_snapshot = relationship('WorkflowSnapshotMeta')

    def __init__(self,
                 workflow_id,
                 run_type,
                 snapshot_id,
                 begin_date=None,
                 end_date=None,
                 status=WorkflowStatus.INIT.value,
                 event_offset=-1,
                 uuid=None):
        self.workflow_id = workflow_id
        self.run_type = run_type
        self.snapshot_id = snapshot_id
        self.begin_date = begin_date
        self.end_date = end_date
        self.status = status
        self.event_offset = event_offset
        self.id = uuid
