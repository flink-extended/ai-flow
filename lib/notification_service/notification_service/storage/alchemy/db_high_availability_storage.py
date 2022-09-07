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

from notification_service.model.member import Member
from sqlalchemy import Column, String, BigInteger, Integer

from notification_service.util import db
from notification_service.util.db import provide_session

from notification_service.storage.alchemy.base import Base
from notification_service.storage.high_availability import HighAvailabilityStorage


class DbHighAvailabilityStorage(HighAvailabilityStorage):

    def __init__(self, db_conn=None):
        if db_conn is not None:
            db.SQL_ALCHEMY_CONN = db_conn
        db.prepare_db()

    def list_living_members(self, ttl_ms):
        return MemberModel.get_living_members(ttl_ms)

    def list_dead_members(self, ttl_ms):
        return MemberModel.get_dead_members(ttl_ms)

    def update_member(self, server_uri, server_uuid):
        MemberModel.update_member(server_uri, server_uuid)

    def delete_member(self, server_uri=None, server_uuid=None):
        MemberModel.delete_member(server_uri, server_uuid)

    def clear_dead_members(self, ttl_ms):
        MemberModel.clear_dead_members(ttl_ms)


class MemberModel(Base):
    __tablename__ = "member_model"
    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    version = Column(BigInteger(), nullable=False)
    server_uri = Column(String(767), nullable=False, unique=True)
    update_time = Column(BigInteger(), nullable=False)
    uuid = Column(String(128), nullable=False, unique=True)

    @staticmethod
    @provide_session
    def update_member(server_uri, server_uuid, session=None):
        member = session.query(MemberModel) \
            .filter(MemberModel.server_uri == server_uri).first()
        if member is None:
            member = MemberModel()
            member.version = 1
            member.server_uri = server_uri
            member.update_time = time.time_ns() / 1000000
            member.uuid = server_uuid
            session.add(member)
        else:
            if member.uuid != server_uuid:
                raise Exception("The server uri '%s' is already exists in the storage!" %
                                server_uri)
            member.version += 1
            member.update_time = time.time_ns() / 1000000
        session.commit()

    @staticmethod
    @provide_session
    def get_living_members(ttl, session=None):
        member_models = session.query(MemberModel) \
            .filter(MemberModel.update_time >= time.time_ns() / 1000000 - ttl) \
            .all()
        return [Member(m.version, m.server_uri, int(m.update_time)) for m in member_models]

    @staticmethod
    @provide_session
    def get_dead_members(ttl, session=None):
        member_models = session.query(MemberModel) \
            .filter(MemberModel.update_time < time.time_ns() / 1000000 - ttl) \
            .all()
        return [Member(m.version, m.server_uri, int(m.update_time)) for m in member_models]

    @staticmethod
    @provide_session
    def delete_member(server_uri=None, server_uuid=None, session=None):
        conditions = []
        if server_uri:
            conditions.append(MemberModel.server_uri == server_uri)
        if server_uuid:
            conditions.append(MemberModel.uuid == server_uuid)
        if len(conditions) != 1:
            raise Exception("Please provide exactly one param, server_uri or server_uuid")
        member = session.query(MemberModel).filter(*conditions).first()
        if member is not None:
            session.delete(member)
        session.commit()

    @staticmethod
    @provide_session
    def clear_dead_members(ttl, session=None):
        session.query(MemberModel) \
            .filter(MemberModel.update_time < time.time_ns() / 1000000 - ttl) \
            .delete()
        session.commit()
