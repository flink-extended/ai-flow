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
import time
import socket
from collections import Iterable
from typing import Union, Tuple

from notification_service.model.event import Event, ANY_CONDITION
from notification_service.model.sender_event_count import SenderEventCount
from notification_service.mongo_notification import MongoEvent, MongoClientModel
from notification_service.storage.event_storage import BaseEventStorage

from mongoengine import connect
from mongoengine import Document, StringField, SequenceField, LongField, BooleanField


class MongoEventStorage(BaseEventStorage):
    def __init__(self, *args, **kwargs):
        self.db_conn = self.setup_connection(**kwargs)
        self.db = None
        self.server_ip = socket.gethostbyname(socket.gethostname())

    def setup_connection(self, **kwargs):
        db_conf = {
            "host": kwargs.get("host"),
            "port": kwargs.get("port"),
            "db": kwargs.get("db"),
        }
        self.db = db_conf.get('db')
        username = kwargs.get("username", None)
        password = kwargs.get("password", None)
        authentication_source = kwargs.get("authentication_source", "admin")
        if (username or password) and not (username and password):
            raise Exception("Please provide valid username and password")
        if username and password:
            db_conf.update({
                "username": username,
                "password": password,
                "authentication_source": authentication_source
            })
        return connect(**db_conf)

    def get_latest_version(self, key: str, namespace: str = None):
        mongo_events = MongoEvent.get_by_key(key, 0, 1, "-version")
        if not mongo_events:
            return 0
        return mongo_events[0].version

    def add_event(self, event: Event, uuid: str):
        kwargs = {
            "server_ip": self.server_ip,
            "create_time": int(time.time() * 1000),
            "event_type": event.event_key.event_type,
            "key": event.event_key.name,
            "value": event.message,
            "context": event.context,
            "namespace": event.event_key.namespace,
            "sender": event.event_key.sender,
            "uuid": uuid
        }
        mongo_event = MongoEvent(**kwargs)
        mongo_event.save()
        mongo_event.reload()
        event.create_time = mongo_event.create_time
        event.version = mongo_event.version
        return event

    def list_events(self,
                    key: Union[str, Tuple[str]],
                    version: int = None,
                    event_type: str = None,
                    start_time: int = None,
                    namespace: str = None,
                    sender: str = None):
        key = None if key == "" else key
        version = None if version == 0 else version
        event_type = None if event_type == "" else event_type
        namespace = None if namespace == "" else namespace
        sender = None if sender == "" else sender
        if isinstance(key, str):
            key = (key,)
        elif isinstance(key, Iterable):
            key = tuple(key)
        res = MongoEvent.get_base_events(key, version, event_type, start_time, namespace, sender)
        return res

    def count_events(self,
                     key: Union[str, Tuple[str]],
                     version: int = None,
                     event_type: str = None,
                     start_time: int = None,
                     namespace: str = None,
                     sender: str = None):
        key = None if key == "" else key
        version = None if version == 0 else version
        event_type = None if event_type == "" else event_type
        namespace = None if namespace == "" else namespace
        sender = None if sender == "" else sender
        if isinstance(key, str):
            key = (key,)
        elif isinstance(key, Iterable):
            key = tuple(key)
        res = MongoEvent.count_base_events(key, version, event_type, start_time, namespace, sender)
        return res

    def list_all_events(self, start_time: int):
        res = MongoEvent.get_base_events_by_time(start_time)
        return res

    def list_all_events_from_version(self, start_version: int, end_version: int = None):
        res = MongoEvent.get_base_events_by_version(start_version, end_version)
        return res

    def register_client(self, namespace: str = None, sender: str = None) -> int:
        client = MongoClientModel(namespace=namespace, sender=sender, create_time=int(time.time() * 1000))
        client.save()
        return client.id

    def delete_client(self, client_id):
        client_to_delete = MongoClientModel.objects(id=client_id).first()
        if client_to_delete is None:
            raise Exception("You are trying to delete an non-existing notification client!")
        client_to_delete.is_deleted = True
        client_to_delete.save()

    def is_client_exists(self, client_id) -> bool:
        client_to_check = MongoClientModel.objects(id=client_id, is_deleted__ne=True).first()
        return client_to_check is not None

    def get_event_by_uuid(self, uuid: str):
        return MongoEvent.get_event_by_uuid(uuid)

    def timestamp_to_event_offset(self, timestamp: int) -> int:
        mongo_events = MongoEvent.timestamp_to_event_offset(timestamp=timestamp)
        if not mongo_events:
            return None
        return mongo_events[0].version

    def clean_up(self):
        MongoEvent.delete_by_client(self.server_ip)
        if self.db is not None:
            self.db_conn.drop_database(self.db)


class MongoEvent(Document):
    server_ip = StringField()   # track server that the event belongs to
    key = StringField()
    value = StringField()
    event_type = StringField()
    version = SequenceField()  # use 'version' as the auto increase id
    create_time = LongField()
    context = StringField()
    namespace = StringField()
    sender = StringField()
    uuid = StringField()

    def to_dict(self):
        return {
            "key": self.key,
            "value": self.value,
            "event_type": self.event_type,
            "version": int(self.version),
            "create_time": self.create_time,
            "context": self.context,
            "namespace": self.namespace,
            "sender": self.sender
        }

    def to_base_event(self):
        base_event = Event(**self.to_dict())
        return base_event

    @classmethod
    def convert_to_base_events(cls, mongo_events: list = None):
        if not mongo_events:
            return []
        base_events = []
        for mongo_event in mongo_events:
            base_events.append(mongo_event.to_base_event())
        return base_events

    @classmethod
    def convert_to_event_counts(cls, mongo_counts: list = None):
        if not mongo_counts:
            return []
        event_counts = []
        for mongo_count in mongo_counts:
            event_counts.append(SenderEventCount(sender=mongo_count.sender, event_count=mongo_count.count))
        return event_counts

    @classmethod
    def get_base_events_by_version(cls, start_version: int, end_version: int = None):
        conditions = dict()
        conditions["version__gt"] = start_version
        if end_version is not None and end_version > 0:
            conditions["version__lte"] = end_version
        mongo_events = cls.objects(**conditions).order_by("version")
        return cls.convert_to_base_events(mongo_events)

    @classmethod
    def get_base_events(cls,
                        key: Tuple[str],
                        version: int = None,
                        event_type: str = None,
                        start_time: int = None,
                        namespace: str = None,
                        sender: str = None):
        conditions = dict()
        if len(key) == 1:
            if ANY_CONDITION != key[0]:
                conditions["key"] = key[0]
        elif len(key) > 1:
            conditions["key__in"] = list(key)
        if version is not None and version > 0:
            conditions["version__gt"] = version
        if event_type is not None:
            if event_type != ANY_CONDITION:
                conditions["event_type"] = event_type
        if start_time is not None and start_time > 0:
            conditions["start_time_gte"] = start_time
        if ANY_CONDITION != namespace:
            conditions["namespace"] = namespace
        if sender is not None and ANY_CONDITION != sender:
            conditions["sender"] = sender
        mongo_events = cls.objects(**conditions).order_by("version")
        return cls.convert_to_base_events(mongo_events)

    @classmethod
    def count_base_events(cls,
                          key: Tuple[str],
                          version: int = None,
                          event_type: str = None,
                          start_time: int = None,
                          namespace: str = None,
                          sender: str = None):
        conditions = dict()
        if len(key) == 1:
            if ANY_CONDITION != key[0]:
                conditions["key"] = key[0]
        elif len(key) > 1:
            conditions["key__in"] = list(key)
        if version is not None and version > 0:
            conditions["version__gt"] = version
        if event_type is not None:
            if event_type != ANY_CONDITION:
                conditions["event_type"] = event_type
        if start_time is not None and start_time > 0:
            conditions["start_time_gte"] = start_time
        if ANY_CONDITION != namespace:
            conditions["namespace"] = namespace
        if sender is not None and ANY_CONDITION != sender:
            conditions["sender"] = sender
        mongo_counts = cls.objects(**conditions).aggregate([{"$group": {"_id": "$sender", "count": {"$sum": 1}}}])
        return cls.convert_to_event_counts(mongo_counts)

    @classmethod
    def get_base_events_by_time(cls, create_time: int = None):
        mongo_events = cls.objects(create_time__gte=create_time).order_by("version")
        return cls.convert_to_base_events(mongo_events)

    @classmethod
    def get_by_key(cls, key: str = None, start: int = None, end: int = None, sort_key: str = "version"):
        if key:
            return cls.objects(key=key).order_by(sort_key)[start:end]
        else:
            raise Exception("key is empty, please provide valid key")

    @classmethod
    def delete_by_client(cls, server_ip):
        cls.objects(server_ip=server_ip).delete()

    @classmethod
    def get_event_by_uuid(cls, uuid):
        event = cls.objects(uuid=uuid).first()
        return event.to_base_event()


class MongoClientModel(Document):
    id = SequenceField(primary_key=True)
    namespace = StringField()
    sender = StringField()
    create_time = LongField()
    is_deleted = BooleanField(default=False)

    def __repr__(self):
        return '<Document Client ({}, {}, {}, {})>'.format(
            self.id,
            self.namespace,
            self.sender,
            self.is_deleted)
