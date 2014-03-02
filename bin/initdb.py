#!/usr/bin/env python

import os

import requests
import requests.auth as auth

if os.environ.get('BAUBLE_ENV', None) == "development" or os.environ.get('TRAVIS', None):
    server = "http://localhost:9090"
else:
    server = 'http://api.bauble.io'

api_root = server + "/v1"
url = api_root + "/admin/initdb"

response = requests.post(url)
try:
    response.raise_for_status()
except Exception as exc:
    print(exc)
    print("** Could not initialize the database.")
