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
"""DB command"""
import logging

from notification_service.settings import get_configuration
from notification_service.storage.alchemy.base import Base
from notification_service.util import db

_logger = logging.getLogger(__name__)


def init(args):
    """Init the metadata database"""
    config = get_configuration()
    _logger.info('Initialize the database, db uri: {}'.format(config.db_uri))
    db.upgrade(url=config.db_uri)


def reset(args):
    """Reset the metadata database"""
    config = get_configuration()
    _logger.info('Reset the database, db uri: {}'.format(config.db_uri))
    if args.yes or input("This will drop existing tables if they exist. Proceed? (y/n)").upper() == "Y":
        db.reset_db(url=config.db_uri, metadata=Base.metadata)
    else:
        _logger.info('Cancel reset the database, db uri: {}'.format(config.db_uri))


def upgrade(args):
    """Upgrade the metadata database"""
    config = get_configuration()
    _logger.info('Upgrade the database, db uri: {}'.format(config.db_uri))
    db.upgrade(url=config.db_uri, version=args.version)


def downgrade(args):
    """Downgrade the metadata database"""
    config = get_configuration()
    _logger.info('Downgrade the database, db uri: {}'.format(config.db_uri))
    db.downgrade(url=config.db_uri, version=args.version)
