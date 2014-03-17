from datetime import datetime, date
import json
import urllib

from bottle import request, response

import bauble.db as db
from bauble.model import Model, SystemModel

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


class OptionsPlugin(object):
    """
    Plugin to add an OPTIONS http method request handler for ever route defined
    in the app. This plugin should be installed after all the routes have been
    setup.

    """
    name = 'options'
    api = 2

    def setup(self, app):
        paths = set([route.rule for route in app.routes])
        for path in paths:
            @app.route(path, method="OPTIONS")
            def options_handler(*args, **kwargs):
                """
                All the CORS and other and other request handler are handled by request hooks
                """
                pass


    def apply(self, callback, route):
        """
        This method doesn't do anything but it's required to be implemented by the
        Bottle plugin system
        """
        return callback



class CORSPlugin(object):
    """
    Bottle.py plugin to add CORS headers to each request.
    """

    name = 'cors'
    api = 2

    def apply(self, callback, route):
        from bauble.routes import set_cors_headers

        def wrapper(*args, **kwargs):
            set_cors_headers()
            return callback(*args, **kwargs)
        return wrapper



class JSONPlugin(object):

    name = 'json'
    api = 2

    def encoder(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError

    def apply(self, callback, route):

        def wrapper(*args, **kwargs):
            response_data = callback(*args, **kwargs)

            ## NOTE: we can't automatically decode our models here because at
            ## this point the request.session is closed and we can't get a user
            ## session (with the correct PG search path) with authenticating
            ## again, it's not impossible but its probably better to avoid the
            ## magic and require a json dict to be explicity returned
            # if isinstance(response_data, (Model, SystemModel)):
            #     session = db.Session()
            #     try:
            #         json_dict = session.merge(response_data).json()
            #         response.content_type = 'application/json'
            #     finally:
            #         session.close()
            #     return json.dumps(json_dict, default=self.encoder)
            #     #return json.dumps(response_data.json(), default=self.encoder)
            if isinstance(response_data, (list, tuple, dict)):
                response.content_type = 'application/json'
                return json.dumps(response_data, default=self.encoder)
            return response_data
        return wrapper


class QueryStringPlugin(object):

    name = 'querystring'
    api = 2


    def apply(self, callback, route):

        def wrapper(*args, **kwargs):
            query_string = request.query_string
            if query_string and query_string.strip() != "":
                for param in query_string.split('&'):
                    if param.strip() == "":
                        continue
                    key, value = param.split('=')
                    value = urllib.parse.unquote_plus(value)
                    if key in request.params:
                        if isinstance(request.params[key], list):
                            request.params[key].append(value)
                        else:
                            request.params[key] = [value]
                    else:
                        request.params[key] = value

            return callback(*args, **kwargs)
        return wrapper
