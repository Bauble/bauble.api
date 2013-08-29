#!/usr/bin/env python
#
# This is mostly just used to setup the Travis test environment
#

import json
import os
import sys

import requests

if os.environ.get('BAUBLE_ENV', None) == "production":
    server = 'http://api.bauble.io'
    response = input("Are you sure you want to run this on " + server + "?")
    if response.lower() != 'y':
        sys.exit()
else:
    server = "http://localhost:9090"

api_root = server + "/api/v1"
user="admin"
password="test"

headers = {
    'accept': 'application/json;depth=1',
    'content-type': 'application/json'
    }

user_data = {
    "username": 'test',
    "email": 'test',
    "password": 'test'
    }

org_data = {
    "name": 'TestOrg',
    "owners": [user_data]
    }

print("creating", org_data['name'], "at", server)

response = requests.post(api_root + "/organization", data=json.dumps(org_data),
                         headers=headers)
assert response.status_code == 201, "status not 201: " + str(response.status_code)
org_json = json.loads(response.text)

# approve the organization
response = requests.post(api_root + org_json['ref'] + "/approve", headers=headers,
              auth=(user,password))
assert response.status_code == 200
