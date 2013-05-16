import json

import bottle
from bottle import request, response
import sqlalchemy as sa
import sqlalchemy.orm as orm

import bauble.db as db
import bauble.i18n
import bauble.model.organization as org
from bauble.server import app, API_ROOT, parse_accept_header, JSON_MIMETYPE, TEXT_MIMETYPE
import bauble.types as types
import bauble.utils as utils

# TODO: create() should return a URL that creates a new database so we
# don't accidentally destroy and existing databsae

ORG_ROOT = API_ROOT + "/organization"
DB_NAME=db.db_url_template.split('/')[-1] 

@app.get(ORG_ROOT)
def get(org_id):
    """
    Return a specific organization.
    """
    accepted = parse_accept_header()
    if JSON_MIMETYPE not in accepted and '*/*' not in accepted:
        raise bottle.HTTPError('406 Not Accepted', 'Expected application/json')

    if request.method == "OPTIONS":
        return {}

    auth_header = request.headers['Authorization']
    user, password = bottle.parse_auth(auth_header)
    session = db.connect(user, password)

    depth = 1
    if 'depth' in accepted[JSON_MIMETYPE]:
        depth = accepted[JSON_MIMETYPE]['depth']

    org = session.query(self.mapped_class).get(org_id)

    response.content_type = '; '.join((JSON_MIMETYPE, "charset=utf8"))
    response_json = obj.json(depth=int(depth))
    session.close()
    return response_json


@app.post(ORG_ROOT)
def create():
    """
    Create a new organization.
    """
    accepted = parse_accept_header()
    if JSON_MIMETYPE not in accepted and '*/*' not in accepted:
        raise bottle.HTTPError('406 Not Accepted', 'Expected application/json')

    if request.method == "OPTIONS":
        return {}

    # make sure the content is JSON
    if JSON_MIMETYPE not in request.headers.get("Content-Type"):
        raise bottle.HTTPError('415 Unsupported Media Type', 'Expected application/json')

    auth_header = request.headers['Authorization']
    user, password = bottle.parse_auth(auth_header)
    session = db.connect(user, password)

    # we assume all requests are in utf-8
    data = json.loads(request.body.read().decode('utf-8'))
    
    if 'name' not in data:
        bottle.abort(400, "The name is required")

    count = session.query(org.Organization).filter_by(name=data['name']).count()
    print('count: ', count)
    if count > 0:
        bottle.abort(400, "An organization with this name already exists")

    organization = org.Organization(**data);
    session.add(organization)
    session.commit()

    response_json = organization.json()
    session.close()

    response.content_type = '; '.join((JSON_MIMETYPE, "charset=utf8"))
    return response_json


@app.put(ORG_ROOT)
def update():
    """
    Update an organization.
    """
    return []


@app.delete(ORG_ROOT)
def delete(org_id):
    """
    Delete an organization.
    """
    if request.method == 'OPTIONS':
        return {}

    auth_header = request.headers['Authorization']
    user, password = bottle.parse_auth(auth_header)
    session = db.connect(user, password)

    org = session.query(Organization).get(org_id)
    session.delete(org)
    session.commit()
    session.close()


