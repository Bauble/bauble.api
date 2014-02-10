
import json

from bottle import route
import sqlalchemy as sa
import sqlalchemy.orm as orm

from bauble import app, API_ROOT
import bauble.mimetype as mimetype
from bauble.middleware import *
from bauble.model import Family, Genus  # , GenusNote, GenusSynonym
import bauble.utils as utils

column_names = [col.name for col in sa.inspect(Genus).columns]

def resolve_genus(next):
    def _wrapped(*args, **kwargs):
        request.genus = request.session.query(Genus).get(request.args['genus_id'])
        if not request.genus:
            bottle.abort(404, "Genus not found")
        return next(*args, **kwargs)
    return _wrapped


@app.get(API_ROOT + "/genus")
@basic_auth
def index_genus():
    # TODO: we're not doing any sanitization or validation...see preggy or validate.py
    genera = request.session.query(Genus)
    q = request.query.q
    if q:
        # TODO: this should be a ilike or something simiar
        genera.filter_by(genus=q)

    # set response type explicitly since the auto json doesn't trigger for
    # lists for some reason
    response.content_type = '; '.join((mimetype.json, "charset=utf8"))
    return json.dumps([genus.json() for genus in genera])


@app.get(API_ROOT + "/genus/<genus_id:int>")
@basic_auth
@resolve_genus
def get_genus(genus_id):
    return request.genus.json()


@app.route(API_ROOT + "/genus/<genus_id:int>", method='PATCH')
@basic_auth
@resolve_genus
def patch_genus(genus_id):
    # create a copy of the request data with only the columns
    data = { col: request.json[col] for col in request.json.keys() if col in column_names }
    for key, value in data.items():
        setattr(request.genus, key, data[key])
    request.session.commit()
    return request.genus.json()


@app.post(API_ROOT + "/genus")
@basic_auth
def post_genus():

    # TODO create a subset of the columns that we consider mutable
    mutable = []

    # create a copy of the request data with only the columns
    data = {col: request.json[col] for col in request.json.keys() if col in column_names}

    # if there isn't a family_id look for a family relation on the request data
    if not 'family_id' in data and 'family' in request.json and isinstance(request.json['family'], dict) and 'id' in request.json['family']:
        data['family_id'] = request.json['family']['id']

    # make a copy of the data for only those fields that are columns
    genus = Genus(**data)
    request.session.add(genus)
    request.session.commit()
    response.status = 201
    return genus.json()


@app.delete(API_ROOT + "/genus/<genus_id:int>")
@basic_auth
@resolve_genus
def delete_genus(genus_id):
    request.session.delete(request.genus)
    request.session.commit()
