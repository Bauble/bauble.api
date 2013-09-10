import datetime

import pytest

import bauble.db as db
from bauble.model.organization import Organization
from bauble.model.user import User
from test import utils

@pytest.fixture()
def org(request):
    print("with_org()")
    session = db.connect()
    org = Organization()
    org.name = utils.random_str()
    owner = User()
    owner.username = utils.random_str()
    org.date_approved = datetime.date.today()
    org.owners = [owner];
    session.add_all([org, owner])
    session.commit()

    #session.begin()
    tables = db.Base.metadata.sorted_tables
    map(lambda t: t.schema=org.pg_schema, tables)
    db.Base.metadata.create_all(session.get_bind(), tables=tables)
    map(lambda t: t.schema=None, tables)
    session.commit()

    def cleanup():
        print("with_org.cleanup()")
        session.delete(org)
        session.delete(owner)
        session.execute("drop schema {};".format(org.pg_schema))
        session.commit()
        session.close()
    request.addfinalizer(cleanup)
    return org
