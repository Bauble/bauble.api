import datetime

import pytest

import bauble.db as db
from bauble.model.organization import Organization
from bauble.model import Family, User
from test import utils

@pytest.fixture
def user_session():
    session = db.connect(test.default_user, test_default_password)
    def cleanup():
        session.close()
    request.addfinalizer(cleanup)
    return session


@pytest.fixture
def session():
    """
    Fixture that provides a session that is not associated with a user
    """
    session = db.connect()
    def cleanup():
        session.close()
    request.addfinalizer(cleanup)
    return session


@pytest.fixture
def admin_session():
    """
    Fixture that provides a session that is not associated with a user
    """
    session = db.connect(admin, 'test')
    def cleanup():
        session.close()
    request.addfinalizer(cleanup)
    return session


@pytest.fixture
def org(request):
    session = db.connect()
    org = Organization()
    org.name = utils.random_str()
    owner = User()
    owner.username = utils.random_str()
    org.date_approved = datetime.date.today()
    org.owners = [owner];
    session.add_all([org, owner])
    session.commit()
    pg_schema = org.pg_schema

    tables = db.Base.metadata.sorted_tables
    for table in tables:
        table.schema = pg_schema
    db.Base.metadata.create_all(session.get_bind(), tables=tables)
    for table in tables:
        table.schema = None

    session.commit()
    session.close()

    def cleanup():
        connection = db.engine.connect()
        db.Base.metadata.drop_all(connection, tables=tables)
        connection.execute("drop schema {} cascade;".format(pg_schema))
    request.addfinalizer(cleanup)
    return org


@pytest.fixture
def default_families(org):
    session = db.connect()
    fields = ["family"]
    family_data = [('SomeFamily',), ('AnotherFamily',)]
