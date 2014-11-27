
import bauble.db as db
from bauble.model import Family
import bauble.utils as utils

from test.fixtures import organization, user, session
import test.api as api
from test.utils import random_str


def test_reset_sequence(session, organization):
    organization = session.merge(organization)
    db.set_session_schema(session, organization.pg_schema)
    family = Family(family=random_str())
    session.add(family)
    session.commit()

    utils.reset_sequence(Family.id, organization.pg_schema)

    # TODO: make sure the next value is correct
