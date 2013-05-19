#!/usr/bin/env python

import os
import sys

import bauble
import bauble.server as server

debug=False

# NOTE: environment variables set in .env will be picked up by
# heroku's foreman
if os.environ.get('BAUBLE_ENV') == "development" or sys.argv[1] == 'local':
    host = 'localhost'
    port = '9090'
else:
    host='api.bauble.io'
    port=80

app = server.start(host=host, port=port)
