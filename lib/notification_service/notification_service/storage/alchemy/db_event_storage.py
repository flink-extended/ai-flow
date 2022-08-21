#
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
                    key: Union[str, Tuple[str]],
                    version: int = None,
                    event_type: str = None,
                    start_time: int = None,
                    namespace: str = None,
                    sender: str = None):
        return EventModel.list_events(key, version, event_type, start_time, namespace, sender)

    def count_events(self,
                     key: Union[str, Tuple[str]],
                     version: int = None,
                     event_type: str = None,
                     start_time: int = None,
                     namespace: str = None,
                     sender: str = None):
        return EventModel.count_events(key, version, event_type, start_time, namespace, sender)

    def list_all_events(self, start_time: int):
        return EventModel.list_all_events(start_time)

    def list_all_events_from_version(self, start_version: int, end_version: int = None):
        return EventModel.list_all_events_from_version(start_version, end_version)

    def get_latest_version(self, key: str, namespace: str = None):
        return EventModel.get_latest_version()

    def register_client(self, namespace: str = None, sender: str = None) -> int:
        return ClientModel.register_client(namespace, sender)

    def delete_client(self, client_id):
        ClientModel.delete_client(client_id)

    def is_client_exists(self, client_id) -> bool:
        return ClientModel.is_client_exists(client_id)

    def get_event_by_uuid(self, uuid: str):
        return EventModel.get_event_by_uuid(uuid)

    def timestamp_to_event_offset(self, timestamp: int) -> int:
        return EventModel.timestamp_to_version(timestamp)

    def clean_up(self):
        tables = set(db.engine.table_names())
        for tbl in reversed(Base.metadata.sorted_tables):
            if tbl.name in tables:
                logging.info('Delete all data from table: {}', tbl.name)
                db.engine.execute(tbl.delete())


class EventModel(Base):
    __tablename__ = "event_model"
    version = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    key = Column(String(1024), nullable=False)
    value = Column(Text())
    event_type = Column(String(1024), server_default="UNDEFINED")
    context = Column(Text())
    namespace = Column(String(1024))
    sender = Column(String(1024))
    create_time = Column(BigInteger(), nullable=False)
    uuid = Column(String(40), nullable=False, unique=True)

    @staticmethod
    @provide_session
    def add_event(event: Event, uuid, session=None):
        event_model = EventModel()
        event_model.key = event.event_key.name
        event_model.value = event.message
        event_model.event_type = event.event_key.event_type
        event_model.context = event.context
        event_model.namespace = event.event_key.namespace
        event_model.create_time = int(time.time() * 1000)
        event_model.uuid = uuid
        event_model.sender = event.event_key.sender
        session.add(event_model)
        session.commit()
        return event_model_to_event(event_model)

    @staticmethod
    @provide_session
    def list_events(key: Union[str, Tuple[str]],
                    version: int = None,
                    event_type: str = None,
                    start_time: int = None,
                    namespace: str = None,
                    sender: str = None,
                    session=None):
        key = None if key == "" else key
        event_type = None if event_type == "" else event_type
        namespace = None if namespace == "" else namespace
        sender = None if sender == "" else sender
        if isinstance(key, str):
            key = (key,)
        elif isinstance(key, Iterable):
            key = tuple(key)
        if key is None:
            raise Exception('key cannot be empty.')

        conditions = []
        if event_type is not None and event_type != ANY_CONDITION:
            conditions.append(EventModel.event_type == event_type)
        if start_time is not None and start_time > 0:
            conditions.append(EventModel.create_time >= start_time)
        if namespace is not None and ANY_CONDITION != namespace:
            conditions.append(EventModel.namespace == namespace)
        if sender is not None and ANY_CONDITION != sender:
            conditions.append(EventModel.sender == sender)
        if version > 0:
            conditions.append(EventModel.version > version)
        if ANY_CONDITION not in key:
            conditions.append(EventModel.key.in_(key))
        event_model_list = session.query(EventModel).filter(*conditions).all()
        return [event_model_to_event(event_model) for event_model in event_model_list]

    @staticmethod
    @provide_session
    def count_events(key: Union[str, Tuple[str]],
                     version: int = None,
                     event_type: str = None,
                     start_time: int = None,
                     namespace: str = None,
                     sender: str = None,
                     session=None):
        key = None if key == "" else key
        event_type = None if event_type == "" else event_type
        namespace = None if namespace == "" else namespace
        sender = None if sender == "" else sender
        if isinstance(key, str):
            key = (key,)
        elif isinstance(key, Iterable):
            key = tuple(key)
        if key is None:
            raise Exception('key cannot be empty.')
        conditions = []
        if event_type is not None and event_type != ANY_CONDITION:
            conditions.append(EventModel.event_type == event_type)
        if start_time is not None and start_time > 0:
            conditions.append(EventModel.create_time >= start_time)
        if namespace is not None and ANY_CONDITION != namespace:
            conditions.append(EventModel.namespace == namespace)
        if sender is not None and ANY_CONDITION != sender:
            conditions.append(EventModel.sender == sender)
        if version > 0:
            conditions.append(EventModel.version > version)
        if ANY_CONDITION not in key:
            conditions.append(EventModel.key.in_(key))

        count_results = session.query(EventModel.sender, func.count('*').label('event_count')).filter(*conditions).group_by(
            EventModel.sender)
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
    def list_all_events_from_version(start_version: int, end_version: int = None, session=None):
        conditions = [
            EventModel.version > start_version
        ]
        if end_version is not None and end_version > 0:
            conditions.append(EventModel.version <= end_version)
        event_model_list = session.query(EventModel).filter(*conditions).all()
        return [event_model_to_event(event_model) for event_model in event_model_list]

    @staticmethod
    @provide_session
    def sync_event(event: Event, uuid, session=None):
        event_model = EventModel()
        event_model.key = event.key
        event_model.value = event.value
        event_model.event_type = event.event_type
        event_model.context = event.context
        event_model.namespace = event.namespace
        event_model.create_time = event.create_time
        event_model.uuid = uuid
        event_model.sender = event.sender
        session.add(event_model)
        session.commit()
        return event_model_to_event(event_model)

    @staticmethod
    @provide_session
    def get_latest_version(session=None):
        event = session.query(EventModel).order_by(EventModel.version.desc()) \
            .limit(1).first()
        if event is not None:
            return event.version
        else:
            return 0

    @staticmethod
    @provide_session
    def timestamp_to_version(timestamp, session=None):
        e = session.query(EventModel).filter(EventModel.create_time >= timestamp) \
            .order_by(EventModel.version.asc()) \
            .limit(1).first()
        if e is None:
            return None
        else:
            return e.version

    @staticmethod
    @provide_session
    def get_event_by_uuid(uuid, session=None):
        conditions = [
            EventModel.uuid == uuid
        ]
        return session.query(EventModel).filter(*conditions).first()
