
import datetime
import os
import uuid

import bcrypt
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
import sqlalchemy.orm as orm

import bauble.error as error
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

db_url = os.environ['DATABASE_URL']


def create_unique_schema():
    session = connect()
    unique_name = "bbl_" + str(uuid.uuid4()).replace("-", "_")
    user_permissions = "NOSUPERUSER NOCREATEDB NOCREATEROLE NOLOGIN INHERIT"
    session.execute("CREATE ROLE {name} {perms};".
                    format(name=unique_name, perms=user_permissions))
    session.execute("CREATE SCHEMA {name} AUTHORIZATION {name};".
                    format(name=unique_name))
    session.commit()
    session.close()
    return unique_name



def authenticate(user, password, session):
    """Authenticate a user and password against the user table.

    Return a user instance if the user instance on success else returns False
    """
    from bauble.model import User
    if isinstance(user, str):
        user = session.query(User).filter_by(username=user).first()

    encode = lambda s: s.encode("utf-8") if s else "".encode("utf-8")
    if user and (user.password and password) and bcrypt.hashpw(encode(password), encode(user.password)) == encode(user.password):
        try:
            tmp_session = connect()
            tmp_user = tmp_session.query(User).get(user.id)
            tmp_user.last_accesseed = datetime.datetime.now()
            tmp_session.commit()
        finally:
            tmp_session.close()

        return user
    return False


def connect(user=None, password=None):
    """The role and password are postgresql roles not bauble users"""

    session = get_session()
    # if no user is passed then don't authenticate against the user table
    if user:
        user = authenticate(user, password, session)
        if not user:
            session.close()
            raise error.AuthenticationError()
        if user.organization and user.organization.pg_schema:
            schema = user.organization.pg_schema
            session.execute("SET search_path TO {schema},public;".\
                                format(schema=schema));

    return session


class HistoryExtension(orm.MapperExtension):
    """
    HistoryExtension is a
    :class:`~sqlalchemy.orm.interfaces.MapperExtension` that is added
    to all clases that inherit from bauble.db.Base so that all
    inserts, updates, and deletes made to the mapped objects are
    recorded in the `history` table.
    """
    def _add(self, operation, mapper, instance):
        """
        Add a new entry to the history table.
        """
        user = None
        # TODO: we need to reenable logging the username for the history entry
        # try:
        #     # if engine.name in ('postgres', 'postgresql'):
        #     #     import bauble.plugins.users as users
        #     #     user = users.current_user()
        # except:
        #     if 'USER' in os.environ and os.environ['USER']:
        #         user = os.environ['USER']
        #     elif 'USERNAME' in os.environ and os.environ['USERNAME']:
        #         user = os.environ['USERNAME']

        row = {}
        for c in mapper.local_table.c:
            row[c.name] = getattr(instance, c.name)
        table = History.__table__
        table.insert(dict(table_name=mapper.local_table.name,
                          table_id=instance.id, values=str(row),
                          operation=operation, user=user,
                          timestamp=datetime.datetime.today())).execute()


    def after_update(self, mapper, connection, instance):
        self._add('update', mapper, instance)


    def after_insert(self, mapper, connection, instance):
        self._add('insert', mapper, instance)


    def after_delete(self, mapper, connection, instance):
        self._add('delete', mapper, instance)



class MapperBase(DeclarativeMeta):
    """
    MapperBase adds the id, _created and _last_updated columns to all
    tables.

    In general there is no reason to use this class directly other
    than to extend it to add more default columns to all the bauble
    tables.
    """
    def __init__(cls, classname, bases, dict_):
        if '__tablename__' in dict_:
            cls.id = sa.Column('id', sa.Integer, primary_key=True,
                               autoincrement=True)
            cls._created = sa.Column('_created', types.DateTime(True),
                                     default=sa.func.now())
            cls._last_updated = sa.Column('_last_updated', types.DateTime(True),
                                          default=sa.func.now(),
                                          onupdate=sa.func.now())

            # cls.__mapper_args__ = {'extension': HistoryExtension()}

        super(MapperBase, cls).__init__(classname, bases, dict_)


engine = None

def get_session():
    global engine
    if not engine:
        engine = sa.create_engine(db_url, pool_size=20)

    return orm.sessionmaker(bind=engine)()


"""

# TODO: these session docs are from bauble1 and need to be updated

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

Base = declarative_base(metaclass=MapperBase)
"""
All tables/mappers in Bauble which use the SQLAlchemy declarative
plugin for declaring tables and mappers should derive from this class.

An instance of :class:`sqlalchemy.ext.declarative.Base`
"""


metadata = Base.metadata
"""The default metadata for all Bauble tables.

An instance of :class:`sqlalchemy.schema.Metadata`
"""


system_metadata = sa.schema.MetaData()
"""The metadata for system level tables.
"""

SystemBase = declarative_base(metaclass=MapperBase, metadata=system_metadata)
"""A mapper for system level tables.  Any tables using base will only be
created once in the database and won't be attached to an organization's schema.
"""


history_base = declarative_base(metadata=metadata)

class History(history_base):
    """
    The history table records ever changed made to every table that
    inherits from :ref:`Base`

    :Table name: history

    :Columns:
      id: :class:`sqlalchemy.types.Integer`
        A unique identifier.
      table_name: :class:`sqlalchemy.types.String`
        The name of the table the change was made on.
      table_id: :class:`sqlalchemy.types.Integer`
        The id in the table of the row that was changed.
      values: :class:`sqlalchemy.types.String`
        The changed values.
      operation: :class:`sqlalchemy.types.String`
        The type of change.  This is usually one of insert, update or delete.
      user: :class:`sqlalchemy.types.String`
        The name of the user who made the change.
      timestamp: :class:`sqlalchemy.types.DateTime`
        When the change was made.
    """
    __tablename__ = 'history'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    table_name = sa.Column(sa.String, nullable=False)
    table_id = sa.Column(sa.Integer, nullable=False, autoincrement=False)
    values = sa.Column(sa.String, nullable=False)
    operation = sa.Column(sa.String, nullable=False)
    user = sa.Column(sa.String)
    timestamp = sa.Column(types.DateTime, nullable=False)
