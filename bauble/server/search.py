#
# Handle search requests
#

import bottle
from bottle import request, response

import bauble.db as db
import bauble.error as error
import bauble.search as search
from bauble.server import app, API_ROOT, parse_accept_header, JSON_MIMETYPE, \
    TEXT_MIMETYPE, enable_cors, parse_auth_header, accept

@app.route(API_ROOT + "/search", method=['OPTIONS', 'GET'])
@accept(JSON_MIMETYPE)
def get_search(depth=1):

    if(request.method == 'OPTIONS'):
        return {}

    auth_header = request.headers.get('Authorization')
    if not auth_header:
        bottle.abort(401, "No Authorization header.")
    username, password = parse_auth_header(auth_header)

    try:
        session = db.connect(username, password)
    except error.AuthenticationError as exc:
        bottle.abort(401)

    query = request.query.q
    if not query:
        raise bottle.HTTPError('400 Bad Request', 'Query parameter is required')

    #session = db.connect()
    results = search.search(query, session)

    # if accepted type was */* or json then we always return json
    response.content_type = '; '.join((JSON_MIMETYPE, "charset=utf8"))
    return {'results': [r.json(depth=depth) for r in results]}
    session.close()
