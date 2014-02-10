
import json
from multiprocessing import Process
import os

from bottle import route
import sqlalchemy as sa
import sqlalchemy.orm as orm

import bauble
import bauble.imp as imp
from bauble.model import Model
from bauble import app, API_ROOT
import bauble.mimetype as mimetype
from bauble.middleware import *
from bauble.model import Organization

column_names = [col.name for col in sa.inspect(Organization).columns]

def resolve_organization(next):
    def _wrapped(*args, **kwargs):
        request.organization = request.session.query(Organization).get(request.args['organization_id'])
        return next(*args, **kwargs)
    return _wrapped


@app.get(API_ROOT + "/organization")
@basic_auth
def index_organization():
    # TODO: we're not doing any sanitization or validation...see preggy or validate.py
    orgs = request.session.query(Organization)
    q = request.query.q
    if q:
        # TODO: this should be a ilike or something simiar
        orgs = orgs.filter_by(name=q)

    # set response type explicitly since the auto json doesn't trigger for
    # lists for some reason
    response.content_type = '; '.join((mimetype.json, "charset=utf8"))
    return json.dumps([organization.json() for organization in orgs])


@app.get(API_ROOT + "/organization/<organization_id:int>")
@basic_auth
@accept(mimetype.json)
@resolve_organization
def get_organization(organization_id):
    return request.organization.json()


@app.route(API_ROOT + "/organization/<organization_id:int>", method='PATCH')
@basic_auth
@resolve_organization
def patch_organization(organization_id):

    # need to drop nonmutable columns like id
    mutable = set('name').intersection(column_names)

    # create a copy of the request data with only the columns
    data = {col: request.json[col] for col in request.json.keys() if col in column_names}
    for key, value in data.items():
        setattr(request.organization, key, data[key])
    request.session.commit()
    return request.organization.json()


@app.post(API_ROOT + "/organization")
#@basic_auth
def post_organization():

    # TODO create a subset of the columns that we consider mutable
    mutable = column_names

    # create a copy of the request data with only the columns
    data = {col: request.json[col] for col in request.json.keys() if col in mutable}

    session = db.Session()
    try:
        # make a copy of the data for only those fields that are columns
        organization = Organization(**data)
        session.add(organization)
        session.commit()
        response.status = 201

        # create the default tables for the organization
        if not organization.pg_schema:
            bottle.abort(500, "Couldn't create the organization's schema")

        #tables = db.Base.metadata.sorted_tables
        metadata = Model.metadata
        tables = metadata.sorted_tables
        for table in tables:
            table.schema = organization.pg_schema
        metadata.create_all(session.get_bind(), tables=tables)

        for table in tables:
            table.schema = None

        return organization.json()
    finally:
        session.close()


@app.delete(API_ROOT + "/organization/<organization_id:int>")
@basic_auth
@resolve_organization
def delete_organization(organization_id):
    request.session.delete(request.organization)
    request.session.commit()


@app.post(API_ROOT + "/organization/<organization_id:int>/approve")
@basic_auth
@resolve_organization
def approve(organization_id):

    if not request.user.is_sysadmin:
        bottle.abort(403, "Only a sysadmin can approve an organization.")

    request.organization.date_approved = datetime.date.today()

    # import the default data
    base_path = os.path.join(os.path.join(*bauble.__path__), 'data')
    request.session.commit()

    # TODO: we should probably do the imports in the background
    # and since we can be reasonably sure they will succeeed then
    # go ahead an return a 200 response
    datamap = {
        'family': os.path.join(base_path, "family.txt"),
        'genus': os.path.join(base_path, 'genus.txt'),
        'genus_synonym': os.path.join(base_path, 'genus_synonym.txt'),
        'geography': os.path.join(base_path, 'geography.txt'),
        'habit': os.path.join(base_path, 'habit.txt')
    }

    # TODO: in test mode we should call imp.from_csv directly but in production
    # we should always do it asynchronously

    if os.environ.get('BAUBLE_TEST', 'false') == 'false':
        imp.from_csv(datamap, request.organization.pg_schema)
    else:
        process = Process(target=imp.from_csv, args=(datamap, request.organization.pg_schema))
        process.start()

    return request.organization.json()



@app.get(API_ROOT + "/organization/<organization_id:int>/<relations:path>")
@basic_auth
@resolve_organization
def get_organization_relation(organization_id, relations):
    mapper = orm.class_mapper(Organization)
    for name in relations.split('/'):
        mapper = getattr(mapper.relationships, name).mapper

    query = request.session.query(Organization, mapper.class_).\
        filter(getattr(Organization, 'id') == organization_id).\
        join(*relations.split('/'))

    response.content_type = '; '.join((mimetype.json, "charset=utf8"))
    return json.dumps([obj.json() for parent, obj in query])



@basic_auth
def approve(self, resource_id):


    user = request.session.query(User).filter_by(username=username).one()
    if not user.is_sysadmin:
        bottle.abort(403, "Only a sysadmin can approve an organization.")

    org = request.session.query(Organization).get(resource_id)
    org.date_approved = datetime.date.today()

    # import the default data
    base_path = os.path.join(os.path.join(*bauble.__path__), 'data')
    session.commit()

    # TODO: we should probably do the imports in the background
    # and since we can be reasonably sure they will succeeed then
    # go ahead an return a 200 response
    datamap = {
        'family': os.path.join(base_path, "family.txt"),
        'genus': os.path.join(base_path, 'genus.txt'),
        'genus_synonym': os.path.join(base_path, 'genus_synonym.txt'),
        'geography': os.path.join(base_path, 'geography.txt'),
        'habit': os.path.join(base_path, 'habit.txt')
    }
    from multiprocessing import Process
    process = Process(target=imp.from_csv, args=(datamap, org.pg_schema))
    process.start()
    # imp.from_csv(datamap, org.pg_schema)
    # session.commit()
    response = org.json()

    return response
