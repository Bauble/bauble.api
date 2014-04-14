
from datetime import datetime, timedelta
import json
from multiprocessing import Process
import os
import smtplib

import bottle
from bottle import request, response
import sqlalchemy as sa
import sqlalchemy.orm as orm

import bauble
import bauble.db as db
import bauble.email as email
import bauble.imp as imp
from bauble.model import Model
from bauble import app, API_ROOT
import bauble.mimetype as mimetype
from bauble.middleware import basic_auth, accept
from bauble.model import Organization, Invitation, User, get_relation
from bauble.utils import create_unique_token


org_column_names = [col.name for col in sa.inspect(Organization).columns]
org_mutable = [col for col in org_column_names
               if col not in ['id', 'pg_schema'] and not col.startswith('_')]

def resolve_organization(next):
    def _wrapped(*args, **kwargs):
        request.organization = request.session.query(Organization).get(request.args['organization_id'])
        return next(*args, **kwargs)
    return _wrapped


def build_embedded(embed, organization):
    data = get_relation(Organization, organization.id, embed, session=request.session)

    if isinstance(data, list):
        return (embed, [obj.json() for obj in data])
    else:
        return (embed, data.json() if data else {})


def org_member_only(next):

    def _wrapped(*args, **kwargs):
        if request.user not in request.organization.users:
            bottle.abort(403, "User is not a member of this organization")

        # call next middleware

        return next(*args, **kwargs)

    return _wrapped

#
#
# TODO: This should be an admin only route.  Temporarily disable it for now.
#
# @app.get(API_ROOT + "/organization")
# @basic_auth
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
@org_member_only
def get_organization(organization_id):

    json_data = request.organization.json()

    if 'embed' in request.params:
        embed_list = request.params.embed if isinstance(request.params.embed, list) \
            else [request.params.embed]
        embedded = map(lambda embed: build_embedded(embed, request.organization), embed_list)
        json_data.update(embedded)

    return json_data


@app.route(API_ROOT + "/organization/<organization_id:int>", method='PATCH')
@basic_auth
@resolve_organization
@org_member_only
def patch_organization(organization_id):

    # create a copy of the request data with only the columns
    data = {col: request.json[col] for col in request.json.keys()
            if col in org_mutable}

    for key, value in data.items():
        setattr(request.organization, key, data[key])
    request.session.commit()
    return request.organization.json()


@app.post(API_ROOT + "/organization")
@basic_auth
def post_organization():

    # TODO: if the requesting user already has an organization_id then raise an error

    # create a copy of the request data with only the columns
    data = {col: request.json[col] for col in request.json.keys()
            if col in org_mutable}

    # use an admin session for creating the organization and importing data
    # into the public schema
    admin_session = db.Session()
    try:
        # make a copy of the data for only those fields that are columns
        organization = Organization(**data)

        owner = admin_session.merge(request.user)
        organization.owners.append(owner)
        owner.is_org_owner = True

        admin_session.add(organization)
        admin_session.commit()
        response.status = 201

        # once the organization has been created it should have it's own
        # postgresql schema
        if not organization.pg_schema:
            bottle.abort(500, "Couldn't create the organization's schema")

        metadata = Model.metadata
        tables = metadata.sorted_tables
        for table in tables:
            table.schema = organization.pg_schema
        metadata.create_all(admin_session.get_bind(), tables=tables)
        admin_session.commit()

        for table in tables:
            table.schema = None

        # import the default data
        base_path = os.path.join(os.path.join(*bauble.__path__), 'data')

        datamap = {
            'family': os.path.join(base_path, "family.txt"),
            'genus': os.path.join(base_path, 'genus.txt'),
            'genus_synonym': os.path.join(base_path, 'genus_synonym.txt'),
            'geography': os.path.join(base_path, 'geography.txt'),
            'habit': os.path.join(base_path, 'habit.txt')
        }

        print("importing default data into", organization.pg_schema)

        # in test mode we should call imp.from_csv directly but in production
        # we should always do it asynchronously
        if os.environ.get('BAUBLE_TEST', 'false') == 'true':
            imp.from_csv({'geography': datamap['geography']}, organization.pg_schema)
        else:
            process = Process(target=imp.from_csv, args=(datamap, organization.pg_schema))
            process.start()

        return organization.json()
    finally:
        admin_session.close()


@app.delete(API_ROOT + "/organization/<organization_id:int>")
@basic_auth
@resolve_organization
@org_member_only
def delete_organization(organization_id):
    if request.user not in request.organization.owners:
        bottle.abort('403', 'Only an organization owner may delete an organization')

    # TODO: we should probably just disable or organization rather than delete
    # all their date
    request.session.delete(request.organization)
    request.session.commit()


@app.post(API_ROOT + "/organization/<organization_id:int>/invite")
@basic_auth
@resolve_organization
@org_member_only
def send_invitation(organization_id):

    token = create_unique_token()
    to_email = request.json['email']
    subject = "Bauble Invitation"

    # make sure a user with this email address doesn't already have an account
    count = request.session.query(User).filter_by(email=to_email).count()
    if count > 0:
        bottle.abort(409, "A user with this email address already has a Bauble account")

    # if a message was provided then send it else use the default message
    try:
        if 'message' in request.json:
            email.send(to_email, subject, request.json['message'])
        else:
            email.send_template(to_email, subject, 'default_invite.txt', {
                'organization': request.organization.name,
                'app_url': os.environ.get("BAUBLE_APP_URL", 'http://app.bauble.io'),
                'token': token
            })
    except smtplib.SMTPException as exc:
        print(exc)
        bottle.abort(500, 'Could not send inviation email.')

    invitation = Invitation(**{
        'email': to_email,
        'organization_id': request.organization.id,
        'date_sent': datetime.now(),
        'invited_by_id': request.user.id,
        'message': request.json['message'] if 'message' in request.json else None,
        'token': token,
        'token_expiration': datetime.now() + timedelta(weeks=2)
    })

    request.session.add(invitation)
    request.session.commit()
