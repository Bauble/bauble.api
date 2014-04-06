
from datetime import datetime
import json

import requests
import pytest

import bauble.db as db
import test.api as api
from test.fixtures import organization, session, user


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


@pytest.fixture
def invitation_setup(organization, session):
    invitation_setup.organization = session.merge(organization)
    invitation_setup.user = invitation_setup.organization.owners[0]
    invitation_setup.session = session
    db.set_session_schema(session, invitation_setup.organization.pg_schema)
    return invitation_setup


def test_invitation(invitation_setup):
    user = invitation_setup.user
    org = invitation_setup.organization
    session = invitation_setup.session

    invite_email = '{}@bauble.io'.format(api.get_random_name())

    assert len(org.invitations) == 0
    response = requests.post(api.api_root + "/organization/{}/invite".format(org.id),
                             headers={'content-type': 'application/json'},
                             auth=(user.email, user.access_token),
                             data=json.dumps({
                                 'email': invite_email  # doesn't get sent
                             }))
    assert response.status_code == 200, response.text

    session.refresh(org)
    assert len(org.invitations) == 1
    invitation = org.invitations[0]
    assert isinstance(invitation.token, str)
    assert isinstance(invitation.token_expiration, datetime)

    response = requests.post(api.api_root + "/invitation/{}".format(invitation.token),
                             headers={'content-type': 'application/json'},
                             data=json.dumps({
                                 'password': 'random pwd'
                             }))
    response_json = response.json()
    assert response.status_code == 200, response.text
    assert response_json['email'] == invite_email
    assert response_json['access_token'] is not None
    session.refresh(invitation)
    assert invitation.accepted is True
