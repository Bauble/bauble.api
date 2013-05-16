
import json

import requests
import requests.auth as auth

import test.api as test    


def test_organization():
    org_url = test.api_root + "/organization"
    
    # create a new organization
    print("org_url: ", org_url)
    data = {
        "name": "Some Garden"
    }
    
    headers = test.get_headers()
    headers['content-type'] = 'application/json'
    response = requests.post(org_url, data=json.dumps(data), headers=headers, 
                             auth=auth.HTTPBasicAuth(test.user, test.password))
    response.raise_for_status()
    organization = json.loads(response.text)
    assert organization['name'] == data['name']

    # delete the organization
    requests.delete(test.api_root + organization['ref'], 
                    auth=auth.HTTPBasicAuth(test.user, test.password));
    
