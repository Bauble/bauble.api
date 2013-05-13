#!/usr/bin/env python

import sys

import bauble
import bauble.server as server

host='api.bauble.io'
port=80
debug=False

db_url="postgresql://{host}/bauble".format(host=host)

if len(sys.argv) > 1 and sys.argv[1] == 'local':
    host = 'localhost'
    port = '9090'

#db_url='sqlite:///test.db'

app = server.start(host=host, port=port)
