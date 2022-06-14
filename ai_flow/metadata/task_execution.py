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
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, BigInteger, UniqueConstraint
from sqlalchemy.orm import relationship

from ai_flow.metadata.base import Base


class TaskExecutionMeta(Base):
    """
    It represents the metadata of the TaskExecution.
    :param id: The unique identify of the TaskExecution.
    :param workflow_execution_id: The unique identify of the WorkflowExecution.
    :param begin_date: The begin time of the TaskExecution.
    :param end_date: The end time of the TaskExecution.
    :param sequence_number: The sequence number of the TaskExecution
    :param try_number: The number of retries for TaskExecution.
    :param status: The status(Type:TaskStatus) of the TaskExecution.
    """
    __tablename__ = 'task_execution'

    id = Column(BigInteger, autoincrement=True, primary_key=True)
    workflow_execution_id = Column(Integer, ForeignKey('workflow_execution.id'))
    task_name = Column(String(256))
    sequence_number = Column(Integer)
    try_number = Column(Integer, default=0)
    begin_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(String(256))

    workflow_execution = relationship('WorkflowExecutionMeta')

    __table_args__ = (
        UniqueConstraint('workflow_execution_id', 'task_name', 'sequence_number'),
    )

    def __init__(self,
                 workflow_execution_id,
                 task_name):
        self.workflow_execution_id = workflow_execution_id
        self.task_name = task_name
