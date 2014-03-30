import json

import requests
import pytest

import bauble.db as db
import test.api as api
from test.fixtures import session, user

@pytest.fixture
def setup(user, session):
    setup.user = user
    setup.session = session
    return setup


def test_organization(setup):

    org_json = api.create_resource("/organization", {
        'name': 'Test BG'
    }, user=setup.user)

    # make sure we can get the organization resource
    org_json = api.get_resource('/organization/{}'.format(org_json['id']), user=setup.user)
    owner_id = org_json['owners'][0]
    user_json = api.get_resource('/user/{}'.format(owner_id), user=setup.user)
    assert user_json['id'] == owner_id

    # add another user to the organization
    #user2_data = organization.owners[0].json()
    user2_data = setup.user.json()
    user2_data['username'] = api.get_random_name()
    user2_data['email'] = api.get_random_name()
    user2_data['organization'] = org_json
    user2 = api.create_resource("/user", user2_data, user=setup.user)
    assert user2 is not None

    api.delete_resource('/organization/{}'.format(org_json['id']), user=setup.user)
