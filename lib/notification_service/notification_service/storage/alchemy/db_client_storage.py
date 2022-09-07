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
import time
from sqlalchemy import Column, String, BigInteger, Integer, Boolean

from notification_service.util.db import provide_session
from notification_service.storage.alchemy.base import Base


class ClientModel(Base):
    __tablename__ = "notification_client"
    id = Column(BigInteger().with_variant(Integer, "sqlite"), autoincrement=True, primary_key=True)
    namespace = Column(String(1024))
    sender = Column(String(1024))
    create_time = Column(BigInteger)
    is_deleted = Column(Boolean, default=False)

    @staticmethod
    @provide_session
    def register_client(namespace: str = None, sender: str = None, session=None):
        client = ClientModel()
        client.namespace = namespace
        client.sender = sender
        client.create_time = int(time.time() * 1000)
        session.add(client)
        session.commit()
        return client.id

    @staticmethod
    @provide_session
    def delete_client(client_id, session=None):
        client_to_delete = session.query(ClientModel).filter(ClientModel.id == client_id).first()
        if client_to_delete is None:
            raise Exception("You are trying to delete an non-existing notification client!")
        client_to_delete.is_deleted = True
        session.flush()

    @staticmethod
    @provide_session
    def is_client_exists(client_id, session=None):
        client_to_check = session.query(ClientModel).filter(ClientModel.id == client_id,
                                                            ClientModel.is_deleted.is_(False)).first()
        return client_to_check is not None