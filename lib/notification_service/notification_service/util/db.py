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
import contextlib
import re
import time
import logging
import os
import urllib.parse
import sqlalchemy
from enum import Enum
from functools import wraps

from sqlalchemy import create_engine, Column, String, BigInteger, Text, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker


if not hasattr(time, 'time_ns'):
    time.time_ns = lambda: int(time.time() * 1e9)

# use sqlite by default for testing
SQL_ALCHEMY_DB_FILE = 'notification_service.db'
SQL_ALCHEMY_CONN = "sqlite:///" + SQL_ALCHEMY_DB_FILE
engine = None
Session = None

_logger = logging.getLogger(__name__)


"""
List of SQLAlchemy database engines for notification backend storage.
"""

MYSQL = 'mysql'
SQLITE = 'sqlite'
POSTGRES = 'postgresql'
MSSQL = 'mssql'
MONGODB = 'mongodb'

DATABASE_ENGINES = [
    MYSQL,
    SQLITE,
    POSTGRES,
    MSSQL,
    MONGODB,
]


class DBType(str, Enum):
    SQLITE = "sql_lite"
    MYSQL = "mysql"
    MONGODB = "mongodb"

    @staticmethod
    def value_of(db_type):
        if db_type in ('SQL_LITE', 'sql_lite', 'sqlite'):
            return DBType.SQLITE
        elif db_type in ('MYSQL', 'mysql'):
            return DBType.MYSQL
        elif db_type in ('MONGODB', 'mongodb'):
            return DBType.MONGODB
        else:
            raise NotImplementedError


def _get_alembic_config(url):
    from alembic.config import Config

    current_dir = os.path.dirname(os.path.abspath(__file__))
    package_dir = os.path.normpath(os.path.join(current_dir, '..'))
    directory = os.path.join(package_dir, 'migrations')
    config = Config(os.path.join(package_dir, 'alembic.ini'))
    config.set_main_option('script_location', directory.replace('%', '%%'))
    config.set_main_option('sqlalchemy.url', url.replace('%', '%%'))
    return config


def upgrade(url, version=None):
    """Upgrade the database."""
    # alembic adds significant import time, so we import it lazily
    from alembic import command

    _logger.info('Upgrade the database, db uri: {}'.format(url))
    config = _get_alembic_config(url)
    if version is None:
        version = 'heads'
    command.upgrade(config, version)


def clear_db(url, metadata):
    _logger.info('Clear the database, db uri: {}'.format(url))
    engine = sqlalchemy.create_engine(url)
    connection = engine.connect()
    metadata.drop_all(connection)
    # alembic adds significant import time, so we import it lazily
    from alembic.migration import MigrationContext  # noqa

    migration_ctx = MigrationContext.configure(connection)
    version = migration_ctx._version  # noqa pylint: disable=protected-access
    if version.exists(connection):
        version.drop(connection)


def reset_db(url, metadata):
    _logger.info('Reset the database, db uri: {}'.format(url))
    clear_db(url, metadata)
    upgrade(url)


def downgrade(url, version):
    """Upgrade the database."""
    # alembic adds significant import time, so we import it lazily
    from alembic import command

    _logger.info('Downgrade the database, db uri: {}'.format(url))
    config = _get_alembic_config(url)
    command.downgrade(config, version)


def tables_exists(url):
    """Returns whether tables are created"""
    engine_ = create_engine(url)
    if len(engine_.table_names()) > 0:
        return True
    else:
        return False


def extract_db_engine_from_uri(db_uri):
    """
    Parse specified database URI to extract database type. Confirm extracted database engine is
    supported. If database driver is specified, confirm driver passes a plausible regex.
    """
    scheme = urllib.parse.urlparse(db_uri).scheme
    scheme_plus_count = scheme.count('+')

    """validates scheme parsed from DB URI is supported"""
    if scheme_plus_count == 0:
        db_engine = scheme
    elif scheme_plus_count == 1:
        db_engine, _ = scheme.split('+')
    else:
        error_msg = "Invalid database URI: '%s'." % db_uri
        raise Exception(error_msg)

    """validates db_engine parsed from DB URI is supported"""
    if db_engine not in DATABASE_ENGINES:
        error_msg = "Invalid database engine: '%s'." % db_engine
        raise Exception(error_msg)

    return db_engine


def parse_mongo_uri(db_uri):
    """
    Parse MongoDB URI-style string to split up and return credentials

    Args:
        db_uri (string): MongoDB URI-style string
    Return:

    """
    regex_str = r'^(?P<schema>(mongodb:(?:\/{2})?))((?P<user>\w+?):(?P<pwd>(\w+?))@|:@?)(?P<host>(\S+?)):(?P<port>(\d+))(\/(?P<db>(\S+?)))$'
    pattern = re.compile(regex_str)
    m = pattern.match(db_uri)
    if m is None:
        raise Exception('The URI of MongoDB is invalid')
    return m.group('user'), m.group('pwd'), m.group('host'), m.group('port'), m.group('db')


def prepare_db(user_engine=None, user_session=None, print_sql=False):
    global engine
    global Session
    if user_engine is not None and user_session is not None:
        engine = user_engine
        Session = user_session
    if engine is None or Session is None:
        engine_args = {'encoding': "utf-8"}
        if print_sql:
            engine_args['echo'] = True
        engine = create_engine(SQL_ALCHEMY_CONN, **engine_args)
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
    prepare_db()
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


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


def create_all_tables(db_conn=None):
    global SQL_ALCHEMY_CONN
    if db_conn is not None:
        SQL_ALCHEMY_CONN = db_conn
    if not tables_exists(SQL_ALCHEMY_CONN):
        upgrade(url=SQL_ALCHEMY_CONN)
    prepare_db()


# def drop_all_tables(db_conn=None):
#     global SQL_ALCHEMY_CONN
#     if db_conn is not None:
#         SQL_ALCHEMY_CONN = db_conn
#     clear_db(url=SQL_ALCHEMY_CONN)
