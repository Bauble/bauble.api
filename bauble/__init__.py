import os

import bottle
from bottle import request

#
# TODO: check the permissions on this file and only read it if it's only readable
# by the owner of this process
#

API_ROOT = "/api/v1"

bauble_rcfile = os.path.join(os.environ['HOME'], ".bauble.api")

#bottle.debug(True)
application = app = bottle.Bottle()

# read environment variables from the bauble rcfile
if os.path.exists(bauble_rcfile) and os.path.isfile(bauble_rcfile):
    for line in open(bauble_rcfile):
        try:
            name, value = line.split('=')
            if isinstance(name, str) and isinstance(value, str):
                os.environ[name.strip()] = str(value).strip()
        except Exception as exc:
            print(line)
            print(exc)


if 'DATABASE_URL' not in os.environ:
    raise Exception("DATABASE_URL not in environment")


class ArgsPlugin(object):
    """
    Plugin to add an args property to every request that contains the url_args for the route.
    """
    name = 'args'
    api = 2

    def apply(self, callback, route):
        def wrapper(*args, **kwargs):
            request.args = request.environ['route.url_args']
            return callback(*args, **kwargs)
        return wrapper

app.install(ArgsPlugin())

# importing bauble.routes should setup all the endpoints
import bauble.routes
import bauble.error
