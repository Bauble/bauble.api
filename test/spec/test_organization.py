import json
import requests

import test.api as api
from test.fixtures import organization, user

def test_organization(organization):

    # user_data = {
    #     "username": api.get_random_name(),
    #     "fullname": api.get_random_name(),
    #     "title": api.get_random_name(),
    #     "email": api.get_random_name() + "@google.com",
    #     "password": api.get_random_name()
    # }

    # org_data = {
    #     "name": api.get_random_name(),
    #     "owners": [user_data]
    # }

    # create a new organization
    # org = api.create_resource("/organization", org_data)
    # assert org['name'] == org_data['name']
    # print(org)

    # get the org with depth=2 so we can get its relations
    session = organization.get_session()
    organization = session.merge(organization)

    org = api.get_resource('/organization/{}'.format(organization.id), depth=2)

    owner = org['owners'][0]
    user = api.get_resource(owner['ref'])
    assert user['ref'] == owner['ref']

    #user = api.create_resource(org['ref'] + 'user', user_data)
    #assert user['name'] == user_data['name']
    #assert user['org']['ref'] == org['ref']

    # add another user to the organization
    user2_data = organization.owners[0].json(1)
    user2_data['username'] = api.get_random_name()
    user2_data['organization'] = org
    user2 = api.create_resource("/user", user2_data)

    # approve the organization
    response = requests.post(api.api_root + org['ref'] + "/approve",
                            auth=('admin', 'test'))
    assert response.status_code == 200
    org = json.loads(response.text)
    assert org['date_approved'] is not None or org['date_approved'] is not ""

    # delete the organization (should also delete the users)
    #api.delete_resource(org['ref'])
