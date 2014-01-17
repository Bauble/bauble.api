import inspect
import os
import os.path

import bottle
from bottle import request, response

import bauble
import bauble.db as db
import bauble.i18n

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
    if isinstance(error, str):
        return error
    elif error.body:
        return str(error.body)
    elif error.exception:
        return str(error.exception)

common_errors = [400, 403, 404, 406, 409, 415, 500]
for code in common_errors:
    app.error(code)(default_error_handler)

@app.error(401)
def error_handler_401(error):
    enable_cors()
    header = request.headers.get('Authorization')
    if header:
        user, password = bottle.parse_auth(header)
        return "Could not authorize user: {user}".format(user=user)
    else:
        return "No Authorization header."

#
# 480 and up are custom response codes
#
@app.error(480)
def error_handler_480(error):
    return default_error_handler("Account has not been approved")

@app.error(481)
def error_handler_481(error):
    return default_error_handler("Organization account has been suspended")

@app.error(482)
def error_handler_482(error):
    return default_error_handler("User account has been suspended")


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


def parse_auth_header(header=None):
    """Parse the and return a (user, password) tuple.  If not header is passed
    then use the header from the current request.
    """
    if not header:
        header = request.headers.get('Authorization')
    return bottle.parse_auth(header)



class accept:
    """Decorator class to handle parsing the HTTP Accept header.
    """

    def __init__(self, mimetype):
        self.mimetype = mimetype


    def __call__(self, func):
        def inner(*args, **kwargs):
            accepted = parse_accept_header()

            def set_depth(mimetype):
                if 'depth' not in accepted[mimetype]:
                    return
                nonlocal args

                # insert the depth into the argument list
                try:
                    depth = int(accepted[mimetype]['depth'])
                except Exception as exc:
                    bottle.abort(400,"Invalid depth value")

                argspec = inspect.getfullargspec(func)[0]

                # kwargs['depth'] = depth
                if 'depth' in argspec and 'depth' not in kwargs:
                    index = argspec.index('depth')
                    if args and len(args) > index and args[index] is not None:
                        new_args = list(args)
                        new_args[index] = depth
                        args = tuple(new_args)
                    else:
                        kwargs['depth'] = depth
                else:
                    kwargs['depth'] = depth

            if self.mimetype in accepted:
                set_depth(self.mimetype)
            elif '*/*' in accepted:
                set_depth('*/*')
            else:
                bottle.abort(406, 'Expected application/json')
            return func(*args, **kwargs)
        return inner


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


def init():
    """
    Start the Bauble server.
    """
    raise Exception("This method is obsolete")



    import bauble.server.admin
    from . import resource
    import bauble.server.search
    import bauble.server.contact

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
    resource.ReportDefResource()

    # app.run(host=host, port=port, server="gunicorn", reloader=True,
    #         debug=debug)
    return app
