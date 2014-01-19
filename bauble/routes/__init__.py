
from bottle import request, response

from . import family
from . import genus
from . import taxon
from . import accession
from . import plant
from . import location

from . import admin
from . import contact
from . import organization
from . import search
from . import schema
from . import user

from bauble import app


@app.hook('after_request')
def after_request_hook(*args):
    #print('dir(request): ', dir(response));
    #print('response.body: ', response.body);
    #print('request.content: ', request.content);
    pass

@app.hook('before_request')
def before_request_hook():
    # print(request.method + " " + request.path)
    #print('dir(request): ', dir(response));
    #print('response.body: ', response.body);
    #print('request.content: ', request.content);
    pass


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
