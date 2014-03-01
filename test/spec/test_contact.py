import json

import requests

import test.api as api
from test.fixtures import organization, user, session

# TODO: temporarily disable the contact tests until we can 'travis encrypt' it in the
# travis environment
def xtest_contact(organization):
    contact_url = api.api_root + "/contact"
    headers = {'content-type': 'application/json'}
    data = {
        'subject': 'test subject',
        'name': 'Test User',
        'from': 'test@testes.com',
        'message': 'something very important'
    }
    response = requests.post(contact_url, data=json.dumps(data), headers=headers)
    print('response: ', response)
    response.raise_for_status()
