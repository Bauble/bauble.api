
import json

from bottle import route
import sqlalchemy as sa
import sqlalchemy.orm as orm

from bauble import app, API_ROOT
import bauble.mimetype as mimetype
from bauble.middleware import *
from bauble.model import Genus, Accession# AccessionNote, AccessionSynonym
import bauble.utils as utils

column_names = [col.name for col in sa.inspect(Accession).columns]

def resolve_accession(next):
    def _wrapped(*args, **kwargs):
        request.accession = request.session.query(Accession).get(request.args['accession_id'])
        return next(*args, **kwargs)
    return _wrapped


@app.get(API_ROOT + "/accession")
@basic_auth
def index_accession():
    # TODO: we're not doing any sanitization or validation...see preggy or validate.py
    accessions = request.session.query(Accession)
    q = request.query.q
    if q:
        # TODO: this should be a ilike or something simiar
        accessions.filter_by(code=q)

    # set response type explicitly since the auto json doesn't trigger for
    # lists for some reason
    response.content_type = '; '.join((mimetype.json, "charset=utf8"))
    return json.dumps([accession.json() for accession in accessions])


@app.get(API_ROOT + "/accession/<accession_id:int>")
@basic_auth
@resolve_accession
def get_accession(accession_id):
    return request.accession.json()


@app.route(API_ROOT + "/accession/<accession_id:int>", method='PATCH')
@basic_auth
@resolve_accession
def patch_accession(accession_id):
    # create a copy of the request data with only the columns
    data = { col: request.json[col] for col in request.json.keys() if col in column_names }
    for key, value in data.items():
        setattr(request.accession, key, data[key])
    request.session.commit()
    return request.accession.json()


@app.post(API_ROOT + "/accession")
@basic_auth
@resolve_relation('taxon_id', 'taxon')
def post_accession():

    # TODO create a subset of the columns that we consider mutable
    mutable = []

    # create a copy of the request data with only the columns
    data = { col: request.json[col] for col in request.json.keys() if col in column_names }

    # make a copy of the data for only those fields that are columns
    accession = Accession(**data)
    request.session.add(accession)
    request.session.commit()
    response.status = 201
    return accession.json()


@app.delete(API_ROOT + "/accession/<accession_id:int>")
@basic_auth
@resolve_accession
def delete_accession(accession_id):
    request.session.delete(request.accession)
    request.session.commit()
