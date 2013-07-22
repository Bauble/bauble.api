#!/usr/bin/env python

import os
import sys

import bauble
import bauble.server as server

debug=False

if os.environ.get('BAUBLE_ENV') == ("development")  or \
   (len(sys.argv) > 1 and sys.argv[1].lower().startswith("dev")):
    host = '0.0.0.0'
    port = 9090
else:
    host='api.bauble.io'
    port=80

application = server.init()

if __name__ == "__main__":
    application.run(host=host, port=port, reloader=True, debug=debug)

