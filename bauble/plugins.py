from bottle import request

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
