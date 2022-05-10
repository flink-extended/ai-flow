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
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship

from ai_flow.metadata.base import Base


class TaskExecutionMeta(Base):
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

    def __init__(self,
                 workflow_execution_id,
                 task_name):
        self.workflow_execution_id = workflow_execution_id
        self.task_name = task_name
