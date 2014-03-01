
import json

from bottle import route
import sqlalchemy as sa
import sqlalchemy.orm as orm

from bauble import app, API_ROOT
import bauble.mimetype as mimetype
from bauble.middleware import *
from bauble.model import Family, Genus, get_relation  # , GenusNote, GenusSynonym
import bauble.utils as utils

column_names = [col.name for col in sa.inspect(Genus).columns]

def resolve_genus(next):
    def _wrapped(*args, **kwargs):
        request.genus = request.session.query(Genus).get(request.args['genus_id'])
        if not request.genus:
            bottle.abort(404, "Genus not found")
        return next(*args, **kwargs)
    return _wrapped


def build_embedded(embed, genus):
    if embed == 'synonyms':
        data = genus.synonyms
    else:
        data = get_relation(Genus, genus.id, embed, session=request.session)

    if isinstance(data, list):
        return (embed, [obj.json() for obj in data])
    else:
        return (embed, data.json() if data else '{}')



@app.get(API_ROOT + "/genus")
@basic_auth
@filter_param(Genus, column_names)
def index_genus():
    # TODO: we're not doing any sanitization or validation...see preggy or validate.py

    genera = request.filter if request.filter else request.session.query(Genus)
    return [genus.json() for genus in genera]


@app.get(API_ROOT + "/genus/<genus_id:int>")
@basic_auth
@resolve_genus
def get_genus(genus_id):
    json_data = request.genus.json()

    if 'embed' in request.params:
        embed_list = request.params.embed if isinstance(request.params.embed, list) \
            else [request.params.embed]
        embedded = map(lambda embed: build_embedded(embed, request.genus), embed_list)
        json_data.update(embedded)

    return json_data


@app.route(API_ROOT + "/genus/<genus_id:int>", method='PATCH')
@basic_auth
@resolve_genus
def patch_genus(genus_id):

    if not request.json:
        bottle.abort(400, 'The request doesn\'t contain a request body')

    # create a copy of the request data with only the columns
    data = {col: request.json[col] for col in request.json.keys() if col in column_names}
    for key, value in data.items():
        setattr(request.genus, key, data[key])
    request.session.commit()
    return request.genus.json()


@app.post(API_ROOT + "/genus")
@basic_auth
def post_genus():

    if not request.json:
        bottle.abort(400, 'The request doesn\'t contain a request body')

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
