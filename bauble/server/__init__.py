import os
import os.path

import bottle
from bottle import request, response

import bauble
import bauble.db as db
import bauble.i18n
import bauble.search as search

app = bottle.Bottle()

API_ROOT = "/api/v1"
JSON_MIMETYPE = "application/json"
TEXT_MIMETYPE = "text/plain"
HTML_MIMETYPE = "text/html"

cwd = os.path.abspath(bauble.__path__[0])

#
# TODO: Seems like these hardcoded paths should set somewhere else
#
app_dir = os.path.join(cwd, 'app')
lib_dir = os.path.join(app_dir, 'lib')
js_dir = os.path.join(app_dir, 'js')
test_dir = os.path.join(cwd, 'test')

bottle.TEMPLATE_PATH.insert(0, cwd)


def default_error_handler(error):
    # TODO: only print the error when the debug flag is set
    # make sure the error is printed in the log
    print("error: " + str(error))
    enable_cors()
    if error.body:
        return str(error.body)
    elif error.exception:
        return str(error.exception)

@app.error(400)
def error_handler_400(error):
    return default_error_handler(error)

@app.error(401)
def error_handler_401(error):
    enable_cors()
    header = request.headers.get('Authorization')
    if header:
        user, password = bottle.parse_auth(header)
        return "Could not authorize user: {user}".format(user=user)
    else:
        return "No Authorization header."


@app.error(403)
def error_hanndler_403(error):
    return default_error_handler(error)

@app.error(404)
def error_handler_404(error):
    return default_error_handler(error)

@app.error(406)
def error_handler_406(error):
    return default_error_handler(error)

@app.error(415)
def error_handler_415(something):
    return default_error_handler(error)

@app.error(500)
def error_handler_500(error):
    return default_error_handler(error)


@app.hook('before_request')
def enable_cors():
    """
    You need to add some headers to each request.
    Don't use the wildcard '*' for Access-Control-Allow-Origin in production.
    """
    #response.set_header('Access-Control-Allow-Origin', '*')
    response.set_header('Access-Control-Allow-Origin',
                        request.headers.get("Origin"))
    response.set_header('Access-Control-Allow-Methods',
                        'PUT, GET, POST, DELETE, OPTIONS')
    response.set_header('Access-Control-Allow-Headers',
                        'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token, Authorization')
    # print(request.url, "(", request.method, "): ",
    #       [(k, v) for k, v in response.headers.items()])


@app.get('/test')
def test_index():
    return bottle.static_file('index.html', root=test_dir)


@app.get('/test/<filename>')
def test_get(filename):
    return bottle.static_file(filename, root=test_dir)


@app.get('/test/<path:path>/<filename>')
def testlib_get(path, filename):
    parts = path.split('/')
    return bottle.static_file(filename, root=os.path.join(test_dir, *parts))


def parse_accept_header(header=None):
    """
    Parse the Accept header.

    Returns a dict of mimetype keys that map to an accept param dict
    """
    if(not header):
        header = request.headers.get("Accept")

    ranges = [rng.strip() for rng in header.split(',')]

    result = {}
    for rng in ranges:
        params = rng.split(';')
        d = {}
        for param in params[1:]:
            key, value = param.split("=")
            d[key] = value
        result[params[0]] = d

    return result


#
# Handle search requests
#
@app.route(API_ROOT + "/search", method=['OPTIONS', 'GET'])
def get_search():
    #mimetype, depth = parse_accept_header()
    accepted = parse_accept_header()

    # if JSON_MIMETYPE not in accepted and '*/*' not in accepted and request.method != 'OPTIONS':
    #     raise bottle.HTTPError('406 Not Accepted - Expected application/json')
    if JSON_MIMETYPE in accepted:
        mimetype = JSON__MIMETYPE
    elif '*/*' in accepted:
        mimetype = '*/*'
    else:
        raise bottle.HTTPError('406 Not Accepted', 'Expected application/json')

    if(request.method == 'OPTIONS'):
        #return ''
        return {}

    depth = 1
    if 'depth' in accepted[mimetype]:
        depth = accepted[mimetype]['depth']

    query = request.query.q
    if not query:
        raise bottle.HTTPError('400 Bad Request', 'Query parameter is required')

    session = db.connect()
    results = search.search(query, session)

    # if accepted type was */* or json then we always return json
    response.content_type = '; '.join((JSON_MIMETYPE, "charset=utf8"))
    return {'results': [r.json(depth=depth) for r in results]}



def init():
    """
    Start the Bauble server.
    """
    import bauble.server.admin
    import bauble.server.resource as resource

    # first make sure we can connect to the database
    session = None
    try:
        session = db.connect()
        if not session or not session.execute("SELECT 1;").first():
            raise Exception("Could not connect to database: ", os.environ['DATABASE_URL'])
    except Exception as exc:
        print(exc)
        print("** Check the user/pwd in DATABASE_URL?")
    finally:
        if session:
            session.close()

    resource.FamilyResource()
    resource.GenusResource()
    resource.TaxonResource()
    resource.AccessionResource()
    resource.PlantResource()
    resource.LocationResource()
    resource.SourceDetailResource()

    resource.OrganizationResource()
    resource.UserResource()

    # app.run(host=host, port=port, server="gunicorn", reloader=True,
    #         debug=debug)
    return app
