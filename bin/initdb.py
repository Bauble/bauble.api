#!/usr/bin/env python
#
# Populate a new empty database.  This script doesn't try to create or drop a new
# databae so that you need to know what you're doing before you break something.
#
# To create a new database:
# psql -c "create database $DB_NAME with owner=$DB_OWNER;"
#
# To create a new user for the database:
# psql -c "create database $DB_NAME owner $DB_OWNER encoding 'utf8';" -U postgres

import os
import traceback

from alembic import command
from alembic.config import Config
import sqlalchemy

import bauble.db as db
from bauble.model import SystemModel

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

connection = None
transaction = None
try:
    connection = db.engine.connect()
    transaction = connection.begin()
    for table in SystemModel.metadata.sorted_tables:
        if table.exists(connection):
            raise Exception("Table already exists: {}.  Quitting...".format(table.name))

    SystemModel.metadata.create_all(connection)

    # set alembic version to head
    alembic_cfg = Config(os.path.join(project_root, 'alembic.ini'))
    command.stamp(alembic_cfg, "head")

    transaction.commit()
except sqlalchemy.exc.CircularDependencyError as exc:
    for table in exc.cycles:
        print("** Error creating table: {}".format(table))
    transaction.rollback()
except Exception as exc:
    transaction.rollback()
    traceback.print_exc()
finally:
    if connection:
        connection.close()
