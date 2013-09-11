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

    tables = db.Base.metadata.sorted_tables
    for table in tables:
        table.schema = org.pg_schema
    db.Base.metadata.create_all(session.get_bind(), tables=tables)
    for table in tables:
        table.schema = None
    session.commit()

    def cleanup():
        db.Base.metadata.drop_all(session.get_bind(), tables=tables)
        session.delete(org)
        session.delete(owner)
        session.commit()
        #session.expunge_all()  # prevent drop schema from hanging
        session.execute("drop schema {} cascade;".format(org.pg_schema))
        session.commit()
        session.close()
    request.addfinalizer(cleanup)
    return org
