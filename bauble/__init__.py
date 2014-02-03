import os

import bottle
from bottle import request

#
# TODO: check the permissions on this file and only read it if it's only readable
# by the owner of this process
#

API_ROOT = "/api/v1"
bauble_rcfile = os.path.join(os.environ['HOME'], ".bauble.api")

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


app = None
application = None

application = app = bottle.Bottle(autojson=False)  # disable bottle json plugin
import bauble.plugins as plugins

# setup the routes, error handlers and plugins
import bauble.routes
import bauble.error

app.install(plugins.OptionsPlugin())
app.install(plugins.ArgsPlugin())
app.install(plugins.CORSPlugin())
app.install(plugins.JSONPlugin())
