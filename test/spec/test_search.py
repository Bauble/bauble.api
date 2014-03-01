import pytest
import json

import requests

import bauble
import bauble.db as db
import bauble.search as search
import test.api as api
from test.fixtures import organization, session, user


@pytest.fixture
def setup(organization, session):
    setup.organization = session.merge(organization)
    setup.user = setup.organization.owners[0]
    setup.session = session
    db.set_session_schema(session, setup.organization.pg_schema)
    return setup


def test_parser(setup):
    """
    Test the bauble.search.SearchParser
    """
    user = setup.user
    family = api.create_resource('/family', {'family': api.get_random_name()}, user=user)
    parser = bauble.search.SearchParser()
    parser.statement.parseString(family['family'])
    api.delete_resource('/family/{}'.format(family['id']), user)


def get_headers():
    return {'accept': 'application/json'}


def test_search(setup):

    user = setup.user

    family_name = api.get_random_name()
    family = api.create_resource('/family', {'family': family_name}, user=user)

    family2 = api.create_resource('/family', {'family': api.get_random_name()}, user=user)

    # return $http({method: 'GET', url: globals.apiRoot + '/search', params: {'q': value}})
    #         .then(callback);

    response = requests.get(api.api_root + "/search", params={'q': family_name},
                            headers=get_headers(), auth=(user.email, user.access_token))

    assert response.status_code == 200

    response_json = json.loads(response.text)
    assert 'families' in response_json
    families = response_json['families']
    assert len(families) == 1
    assert families[0]['id'] == family['id']

    api.delete_resource('/family/{}'.format(family['id']), user=user)
    api.delete_resource('/family/{}'.format(family2['id']), user=user)
