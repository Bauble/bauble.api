import datetime

import pytest
import sqlalchemy as sa
import sqlalchemy.orm as orm

import bauble.db as db
from bauble.model.organization import Organization
from bauble.model import Family, Genus, Taxon, User
import test.utils as utils
import test

# @pytest.fixture
# def user_session(org):
#     session = db.connect(test.default_user, test_default_password)
#     def cleanup():
#         session.close()
#     request.addfinalizer(cleanup)
#     return session


@pytest.fixture
def session(request):
    """
    Fixture that provides a session that is not associated with a user
    """
    session = db.connect()
    def cleanup():
        print("cleanup session")
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
    owner.password = utils.random_str()
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

    session.expunge_all()
    session.commit()
    session.close()

    def cleanup():
        session = orm.object_session(org)
        if session:
            session.delete(org)
            session.commit()
        connection = db.engine.connect()
        db.Base.metadata.drop_all(connection, tables=tables)
        connection.execute("drop schema {} cascade;".format(pg_schema))
    request.addfinalizer(cleanup)
    return org



# @pytest.fixture
# def user_session(request, org):
#     session = db.connect()
#     session.add(org)
#     db.set_session_schema(session, org.pg_schema)
#     def cleanup():
#         session.close()
#     request.addfinalizer(cleanup)
#     return session

@pytest.fixture
def family(request, session, org):
    session = utils.org_session(session, org)
    family = Family(family=utils.random_str())
    session.add(family)
    session.commit()
    session.close()
    def cleanup():
        session = orm.object_session(family)
        if session:
            session.delete(family)
            session.commit()
    request.addfinalizer(cleanup)
    return family


@pytest.fixture
def genus(user_session, family):
    genus = Genus(family=family, genus=utils.random_str())
    user_session.add(genus)
    user_session.commit()
    user_session.close()
    return genus

@pytest.fixture
def taxon(user_session, genus):
    taxon = Taxon(genus=genus, sp=utils.random_str())
    user_session.add(taxon)
    user_session.commit()
    user_session.close()
    return taxon


@pytest.fixture
def default_families(org):
    session = db.connect()
    fields = ["family"]
    family_data = [('SomeFamily',), ('AnotherFamily',)]
