from . import genus
from . import family

from bauble import app
from bottle import request, response

@app.hook('after_request')
def after_request_hook():
    #print('dir(request): ', dir(response));
    #print('response.body: ', response.body);
    #print('request.content: ', request.content);
    pass
