#
# Handle search requests
#

import json

import bottle
from bottle import request, response

from bauble import app, API_ROOT
import bauble.db as db
import bauble.error as error
import bauble.search as search
from bauble.middleware import *
import bauble.mimetype as mimetype


@app.route(API_ROOT + "/search")
@basic_auth
@accept(mimetype.json)
def get_search(depth=1):
    query = request.query.q
    if not query:
        raise bottle.abort(400, 'Query parameter is required')

    results = search.search(query, request.session)

    # if accepted type was */* or json then we always return json
    response.content_type = '; '.join((mimetype.json, "charset=utf8"))

    data = {}
    for key, values in results.items():
        if len(values) > 0:
            data[key] = [obj.json() for obj in values]
    return data
