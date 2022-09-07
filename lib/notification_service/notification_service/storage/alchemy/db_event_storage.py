#
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
#
import logging
import time
from collections import Iterable
from typing import Tuple, Union

from notification_service.storage.alchemy.db_client_storage import ClientModel
from sqlalchemy import Column, String, BigInteger, Text, Integer, func

from notification_service.model.event import Event, ANY_CONDITION
from notification_service.storage.event_storage import BaseEventStorage
from notification_service.util import db
from notification_service.util.db import provide_session
from notification_service.util.utils import event_model_to_event, count_result_to_sender_event_count

from notification_service.storage.alchemy.base import Base


class DbEventStorage(BaseEventStorage):

    def __init__(self, db_conn=None):
        if db_conn is not None:
            db.SQL_ALCHEMY_CONN = db_conn
        db.prepare_db()

    def add_event(self, event: Event, uuid: str):
        return EventModel.add_event(event, uuid)

    def list_events(self,
                    key: str = None,
                    namespace: str = None,
                    sender: str = None,
                    begin_offset: int = None,
                    end_offset: int = None):
        return EventModel.list_events(key, namespace, sender, begin_offset, end_offset)

    def count_events(self,
                     key: str = None,
                     namespace: str = None,
                     sender: str = None,
                     begin_offset: int = None,
                     end_offset: int = None):
        return EventModel.count_events(key, namespace, sender, begin_offset, end_offset)

    def list_all_events(self, start_time: int):
        return EventModel.list_all_events(start_time)

    def list_all_events_from_offset(self, start_offset: int, end_offset: int = None):
        return EventModel.list_all_events_from_offset(start_offset, end_offset)

    def register_client(self, namespace: str = None, sender: str = None) -> int:
        return ClientModel.register_client(namespace, sender)

    def delete_client(self, client_id):
        ClientModel.delete_client(client_id)

    def is_client_exists(self, client_id) -> bool:
        return ClientModel.is_client_exists(client_id)

    def get_event_by_uuid(self, uuid: str):
        return EventModel.get_event_by_uuid(uuid)

    def timestamp_to_event_offset(self, timestamp: int) -> int:
        return EventModel.timestamp_to_offset(timestamp)

    def clean_up(self):
        tables = set(db.engine.table_names())
        for tbl in reversed(Base.metadata.sorted_tables):
            if tbl.name in tables:
                logging.info('Delete all data from table: {}', tbl.name)
                db.engine.execute(tbl.delete())


class EventModel(Base):
    __tablename__ = "event_model"
    offset = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    key = Column(String(1024), nullable=False)
    value = Column(Text())
    context = Column(Text())
    namespace = Column(String(1024))
    sender = Column(String(1024))
    create_time = Column(BigInteger(), nullable=False)
    uuid = Column(String(40), nullable=False, unique=True)

    @staticmethod
    @provide_session
    def add_event(event: Event, uuid, session=None):
        event_model = EventModel()
        event_model.key = event.key
        event_model.value = event.value
        event_model.context = event.context
        event_model.namespace = event.namespace
        event_model.create_time = int(time.time() * 1000)
        event_model.uuid = uuid
        event_model.sender = event.sender
        session.add(event_model)
        session.commit()
        return event_model_to_event(event_model)

    @staticmethod
    @provide_session
    def list_events(key: str = None,
                    namespace: str = None,
                    sender: str = None,
                    begin_offset: int = None,
                    end_offset: int = None,
                    session=None):
        key = None if key == "" else key
        namespace = None if namespace == "" else namespace
        sender = None if sender == "" else sender

        conditions = []
        if key is not None and ANY_CONDITION != key:
            conditions.append(EventModel.key == key)
        if namespace is not None and ANY_CONDITION != namespace:
            conditions.append(EventModel.namespace == namespace)
        if sender is not None and ANY_CONDITION != sender:
            conditions.append(EventModel.sender == sender)
        if begin_offset and begin_offset > 0:
            conditions.append(EventModel.offset > begin_offset)
        if end_offset and end_offset > 0:
            conditions.append(EventModel.offset <= begin_offset)
        event_model_list = session.query(EventModel).filter(*conditions).all()
        return [event_model_to_event(event_model) for event_model in event_model_list]

    @staticmethod
    @provide_session
    def count_events(key: str = None,
                     namespace: str = None,
                     sender: str = None,
                     begin_offset: int = None,
                     end_offset: int = None,
                     session=None):
        key = None if key == "" else key
        namespace = None if namespace == "" else namespace
        sender = None if sender == "" else sender
        conditions = []
        if key is not None and ANY_CONDITION != key:
            conditions.append(EventModel.key == key)
        if namespace is not None and ANY_CONDITION != namespace:
            conditions.append(EventModel.namespace == namespace)
        if sender is not None and ANY_CONDITION != sender:
            conditions.append(EventModel.sender == sender)
        if begin_offset and begin_offset > 0:
            conditions.append(EventModel.offset > begin_offset)
        if end_offset and end_offset > 0:
            conditions.append(EventModel.offset <= begin_offset)

        count_results = session.query(EventModel.sender, func.count('*').label('event_count'))\
            .filter(*conditions).group_by(EventModel.sender)
        return [count_result_to_sender_event_count(count_result) for count_result in count_results]

    @staticmethod
    @provide_session
    def list_all_events(start_time: int, session=None):
        conditions = [
            EventModel.create_time >= start_time
        ]
        event_model_list = session.query(EventModel).filter(*conditions).all()
        return [event_model_to_event(event_model) for event_model in event_model_list]

    @staticmethod
    @provide_session
    def list_all_events_from_offset(start_offset: int, end_offset: int = None, session=None):
        conditions = [
            EventModel.offset > start_offset
        ]
        if end_offset is not None and end_offset > 0:
            conditions.append(EventModel.offset <= end_offset)
        event_model_list = session.query(EventModel).filter(*conditions).all()
        return [event_model_to_event(event_model) for event_model in event_model_list]

    @staticmethod
    @provide_session
    def timestamp_to_offset(timestamp, session=None):
        e = session.query(EventModel).filter(EventModel.create_time <= timestamp) \
            .order_by(EventModel.offset.desc()) \
            .limit(1).first()
        return e.offset if e else 0

    @staticmethod
    @provide_session
    def get_event_by_uuid(uuid, session=None):
        conditions = [
            EventModel.uuid == uuid
        ]
        return session.query(EventModel).filter(*conditions).first()
