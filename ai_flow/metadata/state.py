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
import cloudpickle
from sqlalchemy import Column, String, Integer, Binary, ForeignKey
from sqlalchemy.orm import relationship

from ai_flow.metadata.base import Base
from ai_flow.model.state import ValueState, StateType


class WorkflowStateMeta(Base):
    """
    It represents the metadata of the WorkflowState.
    :param id: The unique identify of the WorkflowState.
    :param workflow_id: The unique identify of the Workflow.
    :param type: The type of the WorkflowState.
    :param value: The serialized value of the WorkflowState.
    """
    __tablename__ = 'workflow_state'

    name = Column(String(256), primary_key=True)
    workflow_id = Column(Integer, ForeignKey('workflow.id'), primary_key=True)
    type = Column(String(256))
    value = Column(Binary)

    workflow = relationship('WorkflowMeta')

    def __init__(self,
                 workflow_id,
                 name,
                 state_type,
                 value):
        self.workflow_id = workflow_id
        self.name = name
        self.type = state_type
        self.value = value


class WorkflowExecutionStateMeta(Base):
    """
    It represents the metadata of the WorkflowExecutionState.
    :param id: The unique identify of the WorkflowExecutionState.
    :param workflow_execution_id: The unique identify of the WorkflowExecution.
    :param type: The type of the WorkflowExecutionState.
    :param value: The serialized value of the WorkflowExecutionState.
    """
    __tablename__ = 'workflow_execution_state'

    name = Column(String(256), primary_key=True)
    workflow_execution_id = Column(Integer, ForeignKey('workflow_execution.id'), primary_key=True)
    type = Column(String(256))
    value = Column(Binary)

    workflow_execution = relationship('WorkflowExecutionMeta')

    def __init__(self,
                 workflow_execution_id,
                 name,
                 state_type,
                 value):
        self.workflow_execution_id = workflow_execution_id
        self.name = name
        self.type = state_type
        self.value = value


class DBValueState(ValueState):

    def __init__(self,
                 session):
        self.session = session


class DBWorkflowValueState(DBValueState):

    def __init__(self,
                 session,
                 workflow_id,
                 state_name):
        super().__init__(session)
        self.workflow_id = workflow_id
        self.state_name = state_name

    def value(self) -> object:
        meta = self.session.query(WorkflowStateMeta) \
            .filter(WorkflowStateMeta.workflow_id == self.workflow_id,
                    WorkflowStateMeta.name == self.state_name).first()
        if meta is None:
            return None
        else:
            return cloudpickle.loads(meta.value)

    def update(self, state):
        """Do not committed"""
        obj_bytes = cloudpickle.dumps(state)
        meta = self.session.query(WorkflowStateMeta) \
            .filter(WorkflowStateMeta.workflow_id == self.workflow_id,
                    WorkflowStateMeta.name == self.state_name).first()
        if meta is None:
            meta = WorkflowStateMeta(workflow_id=self.workflow_id,
                                     name=self.state_name,
                                     state_type=StateType.VALUE,
                                     value=obj_bytes)
            self.session.add(meta)
        else:
            meta.value = obj_bytes
            self.session.merge(meta)
        self.session.flush()


class DBWorkflowExecutionValueState(DBValueState):

    def __init__(self,
                 session,
                 workflow_execution_id,
                 state_name):
        super().__init__(session)
        self.workflow_execution_id = workflow_execution_id
        self.state_name = state_name

    def value(self) -> object:
        meta = self.session.query(WorkflowExecutionStateMeta) \
            .filter(WorkflowExecutionStateMeta.workflow_execution_id == self.workflow_execution_id,
                    WorkflowExecutionStateMeta.name == self.state_name).first()
        if meta is None:
            return None
        else:
            return cloudpickle.loads(meta.value)

    def update(self, state):
        """Do not committed"""
        obj_bytes = cloudpickle.dumps(state)
        meta = self.session.query(WorkflowExecutionStateMeta) \
            .filter(WorkflowExecutionStateMeta.workflow_execution_id == self.workflow_execution_id,
                    WorkflowExecutionStateMeta.name == self.state_name).first()
        if meta is None:
            meta = WorkflowExecutionStateMeta(workflow_execution_id=self.workflow_execution_id,
                                              name=self.state_name,
                                              state_type=StateType.VALUE,
                                              value=obj_bytes)
            self.session.add(meta)
        else:
            meta.value = obj_bytes
            self.session.merge(meta)
        self.session.flush()

