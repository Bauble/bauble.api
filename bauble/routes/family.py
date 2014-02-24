
import json

import bottle
from bottle import request, response
import sqlalchemy as sa
import sqlalchemy.orm as orm

from bauble import app, API_ROOT
import bauble.mimetype as mimetype
from bauble.middleware import basic_auth, filter_param
from bauble.model import Family, FamilyNote, FamilySynonym, get_relation

column_names = [col.name for col in sa.inspect(Family).columns]

def resolve_family(next):
    def _wrapped(*args, **kwargs):
        request.family = request.session.query(Family).get(request.args['family_id'])
        if not request.family:
            bottle.abort(404, "Family not found")
        return next(*args, **kwargs)
    return _wrapped


def build_embedded(embed, family):
    if embed == 'synonyms':
        data = family.synonyms
    else:
        data = get_relation(Family, family.id, embed, session=request.session)
    return (embed, [obj.json() for obj in data])


@app.get(API_ROOT + "/family")
@basic_auth
@filter_param(Family, column_names)
def index_family():
    # TODO: we're not doing any sanitization or validation...see preggy or validate.py

    families = request.filter if request.filter else request.session.query(Family)
    return [family.json() for family in families]


@app.get(API_ROOT + "/family/<family_id:int>")
@basic_auth
@resolve_family
def get_family(family_id):
    json_data = request.family.json()

    if 'embed' in request.params:
        embed_list = request.params.embed if isinstance(request.params.embed, list) \
            else [request.params.embed]
        embedded = map(lambda embed: build_embedded(embed, request.family), embed_list)
        json_data.update(embedded)

    return json_data


@app.route(API_ROOT + "/family/<family_id:int>", method='PATCH')
@basic_auth
@resolve_family
def patch_family(family_id):

    if not request.json:
        bottle.abort(400, 'The request doesn\'t contain a request body')

    # TODO: restrict the columns to only those that are patchable

    # create a copy of the request data with only the columns
    data = {col: request.json[col] for col in request.json.keys() if col in column_names}
    for key, value in data.items():
        setattr(request.family, key, data[key])
    request.session.commit()

    return request.family.json()


@app.post(API_ROOT + "/family")
@basic_auth
def post_family():

    if not request.json:
        bottle.abort(400, 'The request doesn\'t contain a request body')

    # TODO create a subset of the columns that we consider mutable
    mutable = []

    # create a copy of the request data with only the columns
    data = {col: request.json[col] for col in request.json.keys() if col in column_names}

    # make a copy of the data for only those fields that are columns
    family = Family(**data)
    request.session.add(family)
    request.session.commit()
    response.status = 201
    return family.json()


@app.delete(API_ROOT + "/family/<family_id:int>")
@basic_auth
@resolve_family
def delete_family(family_id):
    request.session.delete(request.family)
    request.session.commit()


@app.get(API_ROOT + "/family/<family_id:int>/synonyms")
@basic_auth
@resolve_family
def list_synonyms(family_id):
    return request.family.synonyms


@app.get(API_ROOT + "/family/<family_id:int>/synonyms/<synonym_id:int>")
@basic_auth
@resolve_family
def get_synonym(family_id, synonym_id):
    return request.family.synonyms


@app.post(API_ROOT + "/family/<family_id:int>/synonyms")
@basic_auth
@resolve_family
def add_synonym(family_id):
    synonym_json = request.json
    if 'id' not in synonym_json:
        bottle.abort(400, "No id in request body")
    syn_family = request.session.query(Family).get(synonym_json['id'])
    print('syn_family.json(): ', syn_family.json())
    request.family.synonyms.append(syn_family)
    request.session.commit()
    response.status = 201


@app.delete(API_ROOT + "/family/<family_id:int>/synonyms/<synonym_id:int>")
@basic_auth
@resolve_family
def remove_synonym_(family_id, synonym_id):
    # :synonym_id is the id of the family not the FamilySynonym object
    synonym_json = request.json
    syn_family_id = synonym_json.id
    syn_family = request.session.query(Family).get(syn_family_id)
    req.family.synonyms.remove(syn_family)


@app.get(API_ROOT + "/family/<family_id:int>/<relations:path>")
@basic_auth
@resolve_family
def get_family_relation(family_id, relations):

    mapper = orm.class_mapper(Family)
    for name in relations.split('/'):
        mapper = getattr(mapper.relationships, name).mapper

    query = request.session.query(Family, mapper.class_).\
        filter(getattr(Family, 'id') == family_id).\
        join(*relations.split('/'))

    response.content_type = '; '.join((mimetype.json, "charset=utf8"))
    return json.dumps([obj.json() for parent, obj in query])



###############################################################
#
# There shouldn't be any routes below here b/c get_family_relations acts as a catch-all
# route.
#
###############################################################
