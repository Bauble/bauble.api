import os

import bottle

API_ROOT = "/v1"

app = None
application = None

application = app = bottle.Bottle(autojson=False)  # disable bottle json plugin
import bauble.plugins as plugins

# setup the routes, error handlers and plugins
import bauble.routes
import bauble.error

app.install(plugins.OptionsPlugin())
app.install(plugins.QueryStringPlugin())
app.install(plugins.ArgsPlugin())
app.install(plugins.CORSPlugin())
app.install(plugins.JSONPlugin())
