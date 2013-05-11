#!/usr/bin/env python

import sys

import bauble
import bauble.server as server

host='0.0.0.0'
port=80
debug=False

db_url="sqlite:///test.db"

if len(sys.argv) > 1:
    host = sys.argv[1]

if len(sys.argv) > 2:
    port = sys.argv[2]

#db_url='sqlite:///test.db'

app = server.start(host=host, port=port, db_url=db_urlp)
