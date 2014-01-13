
import json

from bottle import route
import sqlalchemy as sa
import sqlalchemy.orm as orm

from bauble import app, API_ROOT
import bauble.mimetype as mimetype
from bauble.middleware import *
from bauble.model import Family, Genus# GenusNote, GenusSynonym

column_names = [col.name for col in sa.inspect(Genus).columns]

def resolve_genus(next):
    def _wrapped(*args, **kwargs):
        request.genus = request.session.query(Genus).get(request.args['genus_id'])
        return next(*args, **kwargs)
    return _wrapped


@app.get(API_ROOT + "/genus")
@basic_auth
def index_genus():
    # TODO: we're not doing any sanitization or validation...see preggy or validate.py
    families = request.session.query(Genus)
    q = request.query.q
    if q:
        # TODO: this should be a ilike or something simiar
        families.filter_by(genus=q)

    # set response type explicitly since the auto json doesn't trigger for
    # lists for some reason
    response.content_type = '; '.join((mimetype.json, "charset=utf8"))
    return json.dumps([genus.json() for genus in families])


@app.get(API_ROOT + "/genus/:genus_id")
@basic_auth
@resolve_genus
def get_genus(genus_id):
    return request.genus.json(1)


@app.route(API_ROOT + "/genus/:genus_id", method='PATCH')
@basic_auth
@resolve_genus
def patch_genus(genus_id):
    # create a copy of the request data with only the columns
    data = { col: request.json[col] for col in request.json.keys() if col in column_names }
    for key, value in data.items():
        setattr(request.genus, key, data[key])
    request.session.commit()
    return genus.json()


@app.post(API_ROOT + "/genus")
@basic_auth
def post_genus():

    # TODO create a subset of the columns that we consider mutable
    mutable = []

    # create a copy of the request data with only the columns
    data = { col: request.json[col] for col in request.json.keys() if col in column_names }

    print('data["family"]: ', data["family"]);
    if isinstance(data['family'], dict):
        data[family] = utils.get_ref_id(data['family']['ref'])
    else:
        data[family] = utils.get_ref_id(data['family'])

    # make a copy of the data for only those fields that are columns
    genus = Genus(**data)
    request.session.add(genus)
    request.session.commit()
    response.status = 201
    return genus.json()


@app.delete(API_ROOT + "/genus/:genus_id")
@basic_auth
@resolve_genus
def delete_genus(genus_id):
    request.session.delete(request.genus)
    request.session.commit()


@app.route(API_ROOT + "/genus/schema", method='GET')
@basic_auth
def get_genus_schema():
    pass
