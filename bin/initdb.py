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

import bauble.db as db
from bauble.model import SystemModel

transaction = None
try:
    connection = db.engine.connect()
    transaction = connection.begin()
    for table in SystemModel.metadata.sorted_tables:
        if table.exists(connection):
            raise Exception("Table already exists: {}.  Quitting...".format(table.name))

    SystemModel.metadata.create_all(connection)
    transaction.commit()
except Exception as exc:
    transaction.rollback()
    print(exc)
finally:
    if connection:
        connection.close()
