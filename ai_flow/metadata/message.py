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
import queue
import cloudpickle
from typing import List

from ai_flow.common.util.db_util.session import create_session
from sqlalchemy import Column, String, Integer, Index, asc, LargeBinary
from ai_flow.metadata.base import Base


class MessageMeta(Base):

    __tablename__ = 'message'

    id = Column(Integer, autoincrement=True, primary_key=True)
    type = Column(String(256), nullable=False)
    data = Column(LargeBinary, nullable=False)

    __table_args__ = (
        Index('idx_type', type),
    )

    def __init__(self, obj):
        self.type = self.get_message_type(obj)
        self.data = cloudpickle.dumps(obj)

    @staticmethod
    def get_message_type(obj):
        return type(obj).__name__


class Message(object):
    def __init__(self, msg_id, msg_type, data):
        self.id = msg_id
        self.type = msg_type
        self.data = data

    @staticmethod
    def get_all_messages():
        with create_session() as session:
            metas = session.query(MessageMeta).order_by(asc(MessageMeta.id)).all()
            results: List[Message] = []
            for m in metas:
                results.append(Message(m.id, m.type, m.data))
            return results

    @staticmethod
    def add(obj):
        with create_session() as session:
            try:
                message = MessageMeta(obj)
                session.add(message)
                session.commit()
                return Message(message.id, message.type, message.data)
            except Exception as e:
                session.rollback()
                raise e

    @staticmethod
    def batch_delete(msg_id):
        with create_session() as session:
            try:
                session.query(MessageMeta).filter(MessageMeta.id <= msg_id).delete(synchronize_session=False)
                session.commit()
            except Exception as e:
                session.rollback()
                raise e


class PersistentQueue(queue.Queue):
    def __init__(self, maxsize=0):
        super().__init__(maxsize=maxsize)
        self._load_unprocessed_message()
        self.head: int = None

    def put(self, item, block=True, timeout=None):
        ret = Message.add(item)
        super().put(ret, block, timeout)

    def get(self, block=True, timeout=None):
        meta: Message = super().get(block, timeout)
        self.head = meta.id
        return cloudpickle.loads(meta.data)

    def remove_expired(self):
        Message.batch_delete(self.head)

    def _load_unprocessed_message(self):
        unprocessed = Message.get_all_messages()
        for msg in unprocessed:
            super().put(msg)
