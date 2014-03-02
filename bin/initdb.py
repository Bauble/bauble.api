#!/usr/bin/env python
#
# Call the /v1/admin/initdb route.
#
# curl -S -X POST $OPENSHIFT_PYTHON_IP:$OPENSHIFT_PYTHON_PORT/v1/admin/initdb
#

import os
import sys

import requests

server = "http://localhost:9090"
if len(sys.argv) > 1:
    server = sys.argv[1]

api_root = server + "/v1"
url = api_root + "/admin/initdb"

response = requests.post(url)
try:
    response.raise_for_status()
except Exception as exc:
    print(exc)
    print("** Could not initialize the database.")
