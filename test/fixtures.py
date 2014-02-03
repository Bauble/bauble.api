import datetime

import pytest

import bauble.db as db
from bauble.model.organization import Organization
from bauble.model import Model, Family, Genus, Taxon, User
from test import utils
import test


@pytest.fixture
def user_session(request, org):
    session = db.connect()
    session.add(org)
    db.set_session_schema(session, org.pg_schema)
    def cleanup():
        session.close()
    request.addfinalizer(cleanup)
    return session


@pytest.fixture
def session(request):
    """
    Fixture that provides a session that is not associated with a user
    """
    session = db.Session()
    request.addfinalizer(session.close)
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


@pytest.fixture#(scope="function")
def user(request):
    session = db.Session()
    user = session.query(User).filter_by(username=test.default_user).first()
    if user:
        session.delete(user)
        session.commit()

    user = User(username=test.default_user, password=test.default_password)
    session.add(user)
    session.commit()

    user_id = user.id
    session.close()

    def cleanup():
        session = db.Session()
        session.close()
        user = session.query(User).get(user_id)
        if user:
            session.delete(user)
            session.commit()
        session.close()
    request.addfinalizer(cleanup)

    return user

@pytest.fixture#(scope="function")
def organization(request, user):
    session = db.Session()
    user = session.merge(user)

    org = Organization()
    org.name = utils.random_str()
    org.date_approved = datetime.date.today()

    # TODO: adding an owner should be easier than this
    org.owners.append(user);
    user.is_org_owner = True;
    user.organization = org
    session.add(org)
    session.commit()

    pg_schema = org.pg_schema

    tables = Model.metadata.sorted_tables
    for table in tables:
        table.schema = pg_schema

    Model.metadata.create_all(session.get_bind(), tables=tables)
    for table in tables:
        table.schema = None

    session.commit()
    session.close()

    def cleanup():
        session = db.Session()
        session.delete(org)
        session.commit()
        session.close()
        connection = db.engine.connect()
        Model.metadata.drop_all(connection, tables=tables)
        connection.close()

    request.addfinalizer(cleanup)
    return org



@pytest.fixture
def family(user_session):
    family = Family(family=utils.random_str())
    user_session.add(family)
    user_session.commit()
    user_session.close()
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
