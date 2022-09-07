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
import time
import socket
from collections import Iterable
from typing import Union, Tuple

from notification_service.model.event import Event, ANY_CONDITION
from notification_service.model.sender_event_count import SenderEventCount
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

    def add_event(self, event: Event, uuid: str):
        kwargs = {
            "server_ip": self.server_ip,
            "create_time": int(time.time() * 1000),
            "key": event.key,
            "value": event.value,
            "context": event.context,
            "namespace": event.namespace,
            "sender": event.sender,
            "uuid": uuid
        }
        mongo_event = MongoEvent(**kwargs)
        mongo_event.save()
        mongo_event.reload()
        event.create_time = mongo_event.create_time
        event.offset = mongo_event.offset
        return event

    def list_events(self,
                    key: str = None,
                    namespace: str = None,
                    sender: str = None,
                    begin_offset: int = None,
                    end_offset: int = None):
        key = None if key == "" else key
        namespace = None if namespace == "" else namespace
        sender = None if sender == "" else sender
        res = MongoEvent.get_base_events(key, namespace, sender, begin_offset, end_offset)
        return res

    def count_events(self,
                     key: str = None,
                     namespace: str = None,
                     sender: str = None,
                     begin_offset: int = None,
                     end_offset: int = None):
        key = None if key == "" else key
        namespace = None if namespace == "" else namespace
        sender = None if sender == "" else sender
        res = MongoEvent.count_base_events(key, namespace, sender, begin_offset, end_offset)
        return res

    def list_all_events(self, start_time: int):
        res = MongoEvent.get_base_events_by_time(start_time)
        return res

    def list_all_events_from_offset(self, start_offset: int, end_offset: int = None):
        res = MongoEvent.get_base_events_by_offset(start_offset, end_offset)
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
        return MongoEvent.timestamp_to_event_offset(timestamp=timestamp)

    def clean_up(self):
        MongoEvent.delete_by_client(self.server_ip)
        if self.db is not None:
            self.db_conn.drop_database(self.db)


class MongoEvent(Document):
    server_ip = StringField()   # track server that the event belongs to
    key = StringField()
    value = StringField()
    offset = SequenceField()  # use 'offset' as the auto increase id
    create_time = LongField()
    context = StringField()
    namespace = StringField()
    sender = StringField()
    uuid = StringField()

    def to_dict(self):
        return {
            "key": self.key,
            "value": self.value,
            "offset": int(self.offset),
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
    def get_base_events_by_offset(cls, start_offset: int, end_offset: int = None):
        conditions = dict()
        conditions["offset__gt"] = start_offset
        if end_offset is not None and end_offset > 0:
            conditions["offset__lte"] = end_offset
        mongo_events = cls.objects(**conditions).order_by("offset")
        return cls.convert_to_base_events(mongo_events)

    @classmethod
    def get_base_events(cls,
                        key: str = None,
                        namespace: str = None,
                        sender: str = None,
                        begin_offset: int = None,
                        end_offset: int = None):
        conditions = dict()
        if key and key != ANY_CONDITION:
            conditions["key"] = key
        if namespace and namespace != ANY_CONDITION:
            conditions["namespace"] = namespace
        if sender and sender != ANY_CONDITION:
            conditions["sender"] = sender
        if begin_offset:
            conditions["offset__gt"] = begin_offset
        if end_offset:
            conditions["offset__lte"] = end_offset

        mongo_events = cls.objects(**conditions).order_by("offset")
        return cls.convert_to_base_events(mongo_events)

    @classmethod
    def count_base_events(cls,
                          key: str = None,
                          namespace: str = None,
                          sender: str = None,
                          begin_offset: int = None,
                          end_offset: int = None):
        conditions = dict()
        if key and key != ANY_CONDITION:
            conditions["key"] = key
        if namespace and namespace != ANY_CONDITION:
            conditions["namespace"] = namespace
        if sender and sender != ANY_CONDITION:
            conditions["sender"] = sender
        if begin_offset:
            conditions["offset__gt"] = begin_offset
        if end_offset:
            conditions["offset__lte"] = end_offset
        mongo_counts = cls.objects(**conditions).aggregate([{"$group": {"_id": "$sender", "count": {"$sum": 1}}}])
        return cls.convert_to_event_counts(mongo_counts)

    @classmethod
    def get_base_events_by_time(cls, create_time: int = None):
        mongo_events = cls.objects(create_time__gte=create_time).order_by("offset")
        return cls.convert_to_base_events(mongo_events)

    @classmethod
    def get_by_key(cls, key: str = None, start: int = None, end: int = None, sort_key: str = "offset"):
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

    @classmethod
    def timestamp_to_event_offset(cls, timestamp):
        event = cls.objects(create_time__lte=timestamp).order_by('-offset').first()
        return event.offset if event else 0


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
