
import json

import bottle
from bottle import request, response
import sqlalchemy as sa

from bauble import app, API_ROOT
from bauble.middleware import basic_auth, filter_param
from bauble.model import Taxon  # TaxonNote, TaxonSynonym


column_names = [col.name for col in sa.inspect(Taxon).columns]

def resolve_taxon(next):
    def _wrapped(*args, **kwargs):
        request.taxon = request.session.query(Taxon).get(request.args['taxon_id'])
        if not request.taxon:
            bottle.abort(404, "Taxon not found")
        return next(*args, **kwargs)
    return _wrapped


@app.get(API_ROOT + "/taxon")
@basic_auth
@filter_param(Taxon, column_names)
def index_taxon():
    # TODO: we're not doing any sanitization or validation...see preggy or validate.py

    taxa = request.filter if request.filter else request.session.query(Taxon)
    return [taxon.json() for taxon in taxa]


@app.get(API_ROOT + "/taxon/<taxon_id:int>")
@basic_auth
@resolve_taxon
def get_taxon(taxon_id):
    return request.taxon.json()


@app.route(API_ROOT + "/taxon/<taxon_id:int>", method='PATCH')
@basic_auth
@resolve_taxon
def patch_taxon(taxon_id):

    if not request.taxon:
        bottle.abort(400, 'The request doesn\'t contain a request body')

    # create a copy of the request data with only the columns
    data = {col: request.json[col] for col in request.json.keys() if col in column_names}
    for key, value in data.items():
        setattr(request.taxon, key, data[key])
    request.session.commit()
    return request.taxon.json()


@app.post(API_ROOT + "/taxon")
@basic_auth
def post_taxon():

    if not request.json:
        bottle.abort(400, 'The request doesn\'t contain a request body')

    # TODO create a subset of the columns that we consider mutable
    mutable = []

    # create a copy of the request data with only the columns
    data = {col: request.json[col] for col in request.json.keys() if col in column_names}

    # if there isn't a genus_id look for a genus relation on the request data
    if not 'genus_id' in data and 'genus' in request.json and isinstance(request.json['genus'], dict) and 'id' in request.json['genus']:
        data['genus_id'] = request.json['genus']['id']

    # make a copy of the data for only those fields that are columns
    taxon = Taxon(**data)
    request.session.add(taxon)
    request.session.commit()
    response.status = 201
    return taxon.json()


@app.delete(API_ROOT + "/taxon/<taxon_id:int>")
@basic_auth
@resolve_taxon
def delete_taxon(taxon_id):
    request.session.delete(request.taxon)
    request.session.commit()
