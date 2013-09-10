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
    org.owners = [owner];
    session.add_all([org, owner])
    session.commit()

    def cleanup():
        print("with_org.cleanup()")
        session.delete(org)
        session.delete(owner)
        session.commit()
        session.close()
    request.addfinalizer(cleanup)
    return org
