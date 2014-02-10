import json

import requests
import pytest

import bauble.db as db
import test.api as api
from test.fixtures import organization, session, user, admin_user

@pytest.fixture
def setup(organization, session):
    setup.organization = session.merge(organization)
    setup.user = setup.organization.owners[0]
    setup.session = session
    db.set_session_schema(session, setup.organization.pg_schema)
    return setup


def test_organization(setup, admin_user):

    organization = setup.organization
    session = setup.session
    user = setup.user

    # make sure we can get the organization resource
    org = api.get_resource('/organization/{}'.format(organization.id), user=user)
    owner_id = org['owners'][0]
    user_json = api.get_resource('/user/{}'.format(owner_id), user=user)
    assert user_json['id'] == owner_id

    # add another user to the organization
    #user2_data = organization.owners[0].json()
    user2_data = user.json()
    user2_data['username'] = api.get_random_name()
    user2_data['email'] = api.get_random_name()
    user2_data['organization'] = org
    user2 = api.create_resource("/user", user2_data, user=user)

    # approve the organization
    response = requests.post(api.api_root + '/organization/{}'.format(org['id'])
                             + "/approve", auth=(admin_user.email, admin_user.access_token))

                             #auth=('admin', 'test'))
    assert response.status_code == 200
    org = json.loads(response.text)
    assert org['date_approved'] is not None or org['date_approved'] is not ""

    # the organization and owners are deleted in the test finalizer
    pass
