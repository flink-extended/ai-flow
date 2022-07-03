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
import contextlib
import logging
from functools import wraps

import sqlalchemy
import sqlalchemy.orm
from sqlalchemy.orm import sessionmaker, scoped_session

from ai_flow.common.configuration import config_constants
from ai_flow.common.exception.exceptions import AIFlowDBException
from ai_flow.common.util.db_util.orm_event_handlers import setup_event_handlers

logger = logging.getLogger(__name__)
engine = None
Session = None


def _get_managed_session_maker(SessionMaker):
    """
    Creates session factory for generating exception-safe SQLAlchemy sessions that are available for
    using session context manager. Session generated by session factory is automatically committed
    if no exceptions are encountered within its associated context. If an exception is
    encountered, this session could be rolled back. Session generated by session factory is
    automatically closed when the session's associated context is exited.
    """

    @contextlib.contextmanager
    def make_managed_session():
        """Provide transactional scope around series of session operations."""
        session = SessionMaker()
        try:
            yield session
            session.commit()
        except AIFlowDBException:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise AIFlowDBException(e)
        finally:
            session.close()

    return make_managed_session


def create_sqlalchemy_engine(db_uri, **kwargs):
    """
    Create SQLAlchemy engine with specified database URI to support AIFlow entities backend storage.
    """
    enable_pool = config_constants.SQLALCHEMY_POOL_ENABLED
    options = {}
    if enable_pool and 'sqlite' not in db_uri:
        options['pool_size'] = config_constants.SQLALCHEMY_POOL_SIZE
        options['max_overflow'] = config_constants.SQLALCHEMY_MAX_OVERFLOW
    if 'sqlite' in db_uri:
        options['connect_args'] = {'check_same_thread': False}
        logger.warning("SQLite should be only used in unittests.")
    for k, v in kwargs.items():
        options[k] = v
    logger.info("Create SQLAlchemy engine with options %s", options)
    return sqlalchemy.create_engine(db_uri, **options)


def prepare_session(db_uri=None, db_engine=None):
    global engine
    global Session
    if engine is None or Session is None:
        if db_uri is None:
            db_uri = config_constants.METADATA_BACKEND_URI
        if db_engine is not None:
            engine = db_engine
        else:
            engine = create_sqlalchemy_engine(db_uri)
        setup_event_handlers(engine)
        Session = scoped_session(
            sessionmaker(autocommit=False,
                         autoflush=False,
                         bind=engine,
                         expire_on_commit=False))


def clear_engine_and_session():
    global engine
    global Session
    engine = None
    Session = None


@contextlib.contextmanager
def create_session():
    prepare_session()
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def new_session(db_uri=None, db_engine=None):
    prepare_session(db_uri, db_engine)
    return Session()


def provide_session(func):
    """
    Function decorator that provides a session if it isn't provided.
    If you want to reuse a session or run the function as part of a
    database transaction, you pass it to the function, if not this wrapper
    will create one and close it for you.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        arg_session = 'session'

        func_params = func.__code__.co_varnames
        session_in_args = arg_session in func_params and \
                          func_params.index(arg_session) < len(args)
        session_in_kwargs = arg_session in kwargs

        if session_in_kwargs or session_in_args:
            return func(*args, **kwargs)
        else:
            with create_session() as session:
                kwargs[arg_session] = session
                return func(*args, **kwargs)

    return wrapper