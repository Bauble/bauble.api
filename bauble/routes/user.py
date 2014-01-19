
import json

from bottle import route
import sqlalchemy as sa
import sqlalchemy.orm as orm

from bauble import app, API_ROOT
import bauble.mimetype as mimetype
from bauble.middleware import *
from bauble.model import User

column_names = [col.name for col in sa.inspect(User).columns]

def resolve_user(next):
    def _wrapped(*args, **kwargs):
        request.user = request.session.query(User).get(request.args['user_id'])
        return next(*args, **kwargs)
    return _wrapped


@app.get(API_ROOT + "/user")
@basic_auth
def index_user():
    # TODO: we're not doing any sanitization or validation...see preggy or validate.py
    orgs = request.session.query(User)
    q = request.query.q
    if q:
        # TODO: this should be a ilike or something simiar
        orgs = orgs.filter_by(name=q)

    # set response type explicitly since the auto json doesn't trigger for
    # lists for some reason
    response.content_type = '; '.join((mimetype.json, "charset=utf8"))
    return json.dumps([user.json() for user in orgs])


@app.get(API_ROOT + "/user/<user_id:int>")
@basic_auth
@accept(mimetype.json)
@resolve_user
def get_user(user_id):
    depth = request.accept[mimetype.json]['depth']
    return request.user.json(int(depth))


@app.route(API_ROOT + "/user/<user_id:int>", method='PATCH')
@basic_auth
@resolve_user
def patch_user(user_id):

    # need to drop nonmutable columns like id

    # create a copy of the request data with only the columns
    data = { col: request.json[col] for col in request.json.keys() if col in column_names }
    for key, value in data.items():
        setattr(request.user, key, data[key])
    request.session.commit()
    return request.user.json()


@app.post(API_ROOT + "/user")
@basic_auth
def post_user():

    # TODO create a subset of the columns that we consider mutable
    mutable = []

    # create a copy of the request data with only the columns
    data = { col: request.json[col] for col in request.json.keys() if col in column_names }

    print('data: ', data);

    # make a copy of the data for only those fields that are columns
    user = User(**data)
    request.session.add(user)
    request.session.commit()
    response.status = 201
    return user.json()


@app.delete(API_ROOT + "/user/<user_id:int>")
@basic_auth
@resolve_user
def delete_user(user_id):
    request.session.delete(request.user)
    request.session.commit()


@app.get(API_ROOT + "/user/<user_id:int>/<relations:path>")
@basic_auth
@resolve_user
def get_user_relation(user_id, relations):

    mapper = orm.class_mapper(User)
    for name in relations.split('/'):
        mapper = getattr(mapper.relationships, name).mapper

    query = request.session.query(User, mapper.class_).\
            filter(getattr(User, 'id') == user_id).\
            join(*relations.split('/'))

    response.content_type = '; '.join((mimetype.json, "charset=utf8"))
    return json.dumps([obj.json(1) for parent, obj in query])
