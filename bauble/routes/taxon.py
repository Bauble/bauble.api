
import json

from bottle import route
import sqlalchemy as sa
import sqlalchemy.orm as orm

from bauble import app, API_ROOT
import bauble.mimetype as mimetype
from bauble.middleware import *
from bauble.model import Genus, Taxon  # TaxonNote, TaxonSynonym
import bauble.utils as utils

column_names = [col.name for col in sa.inspect(Taxon).columns]

def resolve_taxon(next):
    def _wrapped(*args, **kwargs):
        request.taxon = request.session.query(Taxon).get(request.args['taxon_id'])
        return next(*args, **kwargs)
    return _wrapped


@app.get(API_ROOT + "/taxon")
@basic_auth
def index_taxon():
    # TODO: we're not doing any sanitization or validation...see preggy or validate.py
    taxa = request.session.query(Taxon)
    q = request.query.q
    if q:
        # TODO: this should be a ilike or something simiar
        taxa.filter_by(taxon=q)

    # set response type explicitly since the auto json doesn't trigger for
    # lists for some reason
    response.content_type = '; '.join((mimetype.json, "charset=utf8"))
    return json.dumps([taxon.json() for taxon in taxa])


@app.get(API_ROOT + "/taxon/<taxon_id:int>")
@basic_auth
@resolve_taxon
def get_taxon(taxon_id):
    return request.taxon.json()


@app.route(API_ROOT + "/taxon/<taxon_id:int>", method='PATCH')
@basic_auth
@resolve_taxon
def patch_taxon(taxon_id):
    # create a copy of the request data with only the columns
    data = { col: request.json[col] for col in request.json.keys() if col in column_names }
    for key, value in data.items():
        setattr(request.taxon, key, data[key])
    request.session.commit()
    return request.taxon.json()


@app.post(API_ROOT + "/taxon")
@basic_auth
def post_taxon():

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
