
import bottle
from bottle import request, response
import sqlalchemy as sa

from bauble import app, API_ROOT
from bauble.middleware import basic_auth, filter_param
from bauble.model import Location


column_names = [col.name for col in sa.inspect(Location).columns]

def resolve_location(next):
    def _wrapped(*args, **kwargs):
        request.location = request.session.query(Location).get(request.args['location_id'])
        return next(*args, **kwargs)
    return _wrapped


@app.get(API_ROOT + "/location")
@basic_auth
@filter_param(Location, column_names)
def index_location():
    # TODO: we're not doing any sanitization or validation...see preggy or validate.py

    locations = request.filter if request.filter else request.session.query(Location)
    return [location.json() for location in locations]


@app.get(API_ROOT + "/location/<location_id:int>")
@basic_auth
@resolve_location
def get_location(location_id):
    return request.location.json(1)


@app.route(API_ROOT + "/location/<location_id:int>", method='PATCH')
@basic_auth
@resolve_location
def patch_location(location_id):
    # create a copy of the request data with only the columns
    data = { col: request.json[col] for col in request.json.keys() if col in column_names }
    for key, value in data.items():
        setattr(request.location, key, data[key])
    request.session.commit()
    return request.location.json()


@app.post(API_ROOT + "/location")
@basic_auth
def post_location():

    # TODO create a subset of the columns that we consider mutable
    mutable = []

    # create a copy of the request data with only the columns
    data = { col: request.json[col] for col in request.json.keys() if col in column_names }

    # make a copy of the data for only those fields that are columns
    location = Location(**data)
    request.session.add(location)
    request.session.commit()
    response.status = 201
    return location.json()


@app.delete(API_ROOT + "/location/<location_id:int>")
@basic_auth
@resolve_location
def delete_location(location_id):
    request.session.delete(request.location)
    request.session.commit()
