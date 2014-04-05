
import datetime
import os
import uuid

import bcrypt
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
import sqlalchemy.orm as orm

import bauble.types as types

"""
"""
admin_username = "admin"

# TODO:
# 1. when a new organization is created the "validator" user creates
# the organization and the owner user
# 2. the validator then sends a verification email to the new user
# 3. when the verification is clicked the user account is activated
# 4. need to set the password on the organization's pg role and
# store it in the organization table...this will at least prevent logging in and if they can login with the admin we're screwed anyways

debug = True if os.environ.get('DEBUG', 'false') == "true" else False
db_url = os.environ['BAUBLE_DB_URL']
engine = sa.create_engine(db_url, pool_size=20, encoding="utf-8", echo=debug)
Session = Session = orm.sessionmaker(bind=engine)


def create_unique_schema():
    session = Session()
    unique_name = "bbl_" + str(uuid.uuid4()).replace("-", "_")
    session.execute("CREATE SCHEMA {name};".format(name=unique_name))
    session.commit()
    session.close()
    return unique_name



def set_session_schema(session, schema):
    def set_schema(session, transaction=None, connection=None):
        session.execute("SET search_path TO {schema},public;".
                        format(schema=schema))
    # set the schema now and after any new transactions have begun since
    # they will be started in a new isolated state
    sa.event.listen(session, "after_begin", set_schema)
    set_schema(session)


# class HistoryExtension(orm.MapperExtension):
#     """
#     HistoryExtension is a
#     :class:`~sqlalchemy.orm.interfaces.MapperExtension` that is added
#     to all clases that inherit from bauble.db.Base so that all
#     inserts, updates, and deletes made to the mapped objects are
#     recorded in the `history` table.
#     """
#     def _add(self, operation, mapper, instance):
#         """
#         Add a new entry to the history table.
#         """
#         user = None
#         # TODO: we need to reenable logging the username for the history entry
#         # try:
#         #     # if engine.name in ('postgres', 'postgresql'):
#         #     #     import bauble.plugins.users as users
#         #     #     user = users.current_user()
#         # except:
#         #     if 'USER' in os.environ and os.environ['USER']:
#         #         user = os.environ['USER']
#         #     elif 'USERNAME' in os.environ and os.environ['USERNAME']:
#         #         user = os.environ['USERNAME']

#         row = {}
#         for c in mapper.local_table.c:
#             row[c.name] = getattr(instance, c.name)
#         table = History.__table__
#         table.insert(dict(table_name=mapper.local_table.name,
#                           table_id=instance.id, values=str(row),
#                           operation=operation, user=user,
#                           timestamp=datetime.datetime.today())).execute()


#     def after_update(self, mapper, connection, instance):
#         self._add('update', mapper, instance)


#     def after_insert(self, mapper, connection, instance):
#         self._add('insert', mapper, instance)


#     def after_delete(self, mapper, connection, instance):
#         self._add('delete', mapper, instance)



"""
bauble.db.Session is created after the database has been opened with
:func:`bauble.db.open()`. bauble.db.Session should be used when you need
to do ORM based activities on a bauble database.  To create a new
Session use::Uncategorized

    session = bauble.db.Session()

When you are finished with the session be sure to close the session
with :func:`session.close()`. Failure to close sessions can lead to
database deadlocks, particularly when using PostgreSQL based
databases.
"""

# history_base = declarative_base(metadata=metadata)

# class History(history_base):
#     """
#     The history table records ever changed made to every table that
#     inherits from :ref:`Base`

#     :Table name: history

#     :Columns:
#       id: :class:`sqlalchemy.types.Integer`
#         A unique identifier.
#       table_name: :class:`sqlalchemy.types.String`
#         The name of the table the change was made on.
#       table_id: :class:`sqlalchemy.types.Integer`
#         The id in the table of the row that was changed.
#       values: :class:`sqlalchemy.types.String`
#         The changed values.
#       operation: :class:`sqlalchemy.types.String`
#         The type of change.  This is usually one of insert, update or delete.
#       user: :class:`sqlalchemy.types.String`
#         The name of the user who made the change.
#       timestamp: :class:`sqlalchemy.types.DateTime`
#         When the change was made.
#     """
#     __tablename__ = 'history'
#     id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
#     table_name = sa.Column(sa.String, nullable=False)
#     table_id = sa.Column(sa.Integer, nullable=False, autoincrement=False)
#     values = sa.Column(sa.String, nullable=False)
#     operation = sa.Column(sa.String, nullable=False)
#     user = sa.Column(sa.String)
#     timestamp = sa.Column(types.DateTime, nullable=False)
