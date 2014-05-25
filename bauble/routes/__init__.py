
from bottle import request, response

from . import auth

from . import family
from . import genus
from . import taxon
from . import accession
from . import source
from . import plant
from . import location
from . import report

from . import organization
from . import search
from . import schema
from . import user
from . import invitation

from bauble import app, API_ROOT


@app.hook('after_request')
def after_request_hook(*args):
    # this can be used for debugging but any other request hooks should be setup in bauble.plugins
    pass

@app.hook('before_request')
def before_request_hook():
    # this can be used for debugging but any other request hooks should be setup in bauble.plugins
    pass



def set_cors_headers():
    """
    You need to add some headers to each request.
    Don't use the wildcard '*' for Access-Control-Allow-Origin in production.
    """
    response.set_header('Access-Control-Allow-Origin',
                        request.headers.get("Origin"))
    response.set_header('Access-Control-Allow-Methods',
                        'PUT, GET, POST, DELETE, OPTIONS, PATCH')
    response.set_header('Access-Control-Allow-Headers',
                        'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token, Authorization')
