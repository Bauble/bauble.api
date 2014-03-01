from datetime import datetime, date, timedelta

import pytest

import bauble.db as db
from bauble.model.organization import Organization
from bauble.model import Model, Family, Genus, Taxon, User
from test import utils
import test

@pytest.fixture()
def session(request):
    """
    Fixture that provides a session that is not associated with a user
    """
    session = db.Session()
    request.addfinalizer(session.close)
    return session


@pytest.fixture()
def user(request):
    session = db.Session()

    user = User(email=utils.random_str() + "@bauble.io",
                username=utils.random_str(),
                password=utils.random_str(),
                access_token=utils.random_str(32),
                access_token_expiration=datetime.now() + timedelta(weeks=2))
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


@pytest.fixture()
def admin_user(request):
    session = db.Session()
    user = User(email=utils.random_str() + "@bauble.io",
                username=utils.random_str(),
                password=utils.random_str(),
                access_token=utils.random_str(32),
                access_token_expiration=datetime.now() + timedelta(weeks=2),
                is_sysadmin=True)
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


# @pytest.fixture()
# def admin_user(user):
#     session = db.Session()
#     user2 = session.merge(user)
#     user2.is_sysadmin = True
#     print("admin user: ", user2.email)
#     session.commit()
#     session.close()
#     return user2


#@pytest.fixture()
@pytest.fixture()
def organization(request, user):
    session = db.Session()
    user = session.merge(user)

    org = Organization()
    org.name = utils.random_str()
    org.date_approved = date.today()

    # TODO: adding an owner should be easier than this
    org.owners.append(user)
    user.is_org_owner = True

    session.add(org)
    session.commit()

    user.organization_id = org.id
    session.commit()
    session.refresh(user)

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



@pytest.fixture()
def family(user_session):
    family = Family(family=utils.random_str())
    user_session.add(family)
    user_session.commit()
    user_session.close()
    return family


@pytest.fixture()
def genus(user_session, family):
    genus = Genus(family=family, genus=utils.random_str())
    user_session.add(genus)
    user_session.commit()
    user_session.close()
    return genus

@pytest.fixture()
def taxon(user_session, genus):
    taxon = Taxon(genus=genus, sp=utils.random_str())
    user_session.add(taxon)
    user_session.commit()
    user_session.close()
    return taxon


@pytest.fixture()
def default_families(org):
    session = db.connect()
    fields = ["family"]
    family_data = [('SomeFamily',), ('AnotherFamily',)]
