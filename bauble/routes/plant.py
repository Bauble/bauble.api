
import bottle
from bottle import request, response
import sqlalchemy as sa

from bauble import app, API_ROOT
from bauble.middleware import basic_auth, filter_param, resolve_relation
from bauble.model import Plant


column_names = [col.name for col in sa.inspect(Plant).columns]

def resolve_plant(next):
    def _wrapped(*args, **kwargs):
        request.plant = request.session.query(Plant).get(request.args['plant_id'])
        return next(*args, **kwargs)
    return _wrapped


@app.get(API_ROOT + "/plant")
@basic_auth
@filter_param(Plant, column_names)
def index_plant():
    # TODO: we're not doing any sanitization or validation...see preggy or validate.py

    plants = request.filter if request.filter else request.session.query(Plant)
    return [plant.json() for plant in plants]


@app.get(API_ROOT + "/plant/<plant_id:int>")
@basic_auth
@resolve_plant
def get_plant(plant_id):
    return request.plant.json()


@app.route(API_ROOT + "/plant/<plant_id:int>", method='PATCH')
@basic_auth
@resolve_plant
def patch_plant(plant_id):
    # create a copy of the request data with only the columns
    data = { col: request.json[col] for col in request.json.keys() if col in column_names }
    for key, value in data.items():
        setattr(request.plant, key, data[key])
    request.session.commit()
    return request.plant.json()


@app.post(API_ROOT + "/plant")
@basic_auth
@resolve_relation('accession_id', 'accession')
@resolve_relation('location_id', 'location')
def post_plant():
    # TODO create a subset of the columns that we consider mutable
    mutable = []

    # create a copy of the request data with only the columns
    data = {col: request.json[col] for col in request.json.keys()
            if col in column_names}

    # make a copy of the data for only those fields that are columns
    plant = Plant(**data)
    request.session.add(plant)
    request.session.commit()
    response.status = 201
    return plant.json()


@app.delete(API_ROOT + "/plant/<plant_id:int>")
@basic_auth
@resolve_plant
def delete_plant(plant_id):
    request.session.delete(request.plant)
    request.session.commit()
