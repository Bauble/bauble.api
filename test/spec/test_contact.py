import json

import requests
import requests.auth as auth

import test.api as api

def test_contact():
    contact_url = api.api_root + "/contact"
    headers = { 'content-type': 'application/json' }
    data = {
        'subject': 'test subject',
        'name': 'Test User',
        'from': 'test@testes.com',
        'message': 'something very important'
        }
    response = requests.post(contact_url, data=json.dumps(data), headers=headers)
    print('response: ', response)
    response.raise_for_status()
