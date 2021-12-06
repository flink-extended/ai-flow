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

import logging
from ai_flow.util import sqlalchemy_db
from ai_flow.store.db.base_model import base
from ai_flow.settings import get_configuration

_logger = logging.getLogger(__name__)


def init(args):
    """Init the metadata database"""
    config = get_configuration()
    _logger.info('Initialize the database, db uri: {}'.format(config.get_db_uri()))
    sqlalchemy_db.upgrade(url=config.get_db_uri())


def reset(args):
    """Reset the metadata database"""
    config = get_configuration()
    _logger.info('Reset the database, db uri: {}'.format(config.get_db_uri()))
    if args.yes or input("This will drop existing tables if they exist. Proceed? (y/n)").upper() == "Y":
        sqlalchemy_db.reset_db(url=config.get_db_uri(), metadata=base.metadata)
    else:
        _logger.info('Cancel reset the database, db uri: {}'.format(config.get_db_uri()))


def upgrade(args):
    """Upgrade the metadata database"""
    config = get_configuration()
    _logger.info('Upgrade the database, db uri: {}'.format(config.get_db_uri()))
    sqlalchemy_db.upgrade(url=config.get_db_uri(), version=args.version)


def downgrade(args):
    """Downgrade the metadata database"""
    config = get_configuration()
    _logger.info('Downgrade the database, db uri: {}'.format(config.get_db_uri()))
    sqlalchemy_db.downgrade(url=config.get_db_uri(), version=args.version)
