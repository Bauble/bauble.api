import json

import requests

import bauble
import bauble.search# as search
import test.api as api
from test.fixtures import organization, user


def test_parser(organization):
    """
    Test the bauble.search.SearchParser
    """
    import bauble.search as search
    family = api.create_resource('/family', {'family': api.get_random_name()})
    parser = bauble.search.SearchParser()
    parser.statement.parseString(family['family'])
    api.delete_resource(family)


def get_headers():
    return {'accept': 'application/json'}


def test_search(organization):
    family_name = api.get_random_name()
    family = api.create_resource('/family', {'family': family_name})

    family2 = api.create_resource('/family', {'family': api.get_random_name()})

    # return $http({method: 'GET', url: globals.apiRoot + '/search', params: {'q': value}})
    #         .then(callback);

    response = requests.get(api.api_root + "/search", params={'q': family_name},
                            headers=get_headers(),
                            auth=(api.default_user, api.default_password))
    assert response.status_code == 200

    response_json = json.loads(response.text)
    results = response_json['results']
    # make sure we only get the one we searched for
    assert len(results) == 1

    assert results[0]['ref'] == family['ref']

    api.delete_resource(family['ref'])
    api.delete_resource(family2['ref'])
