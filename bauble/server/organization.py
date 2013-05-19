import json
import uuid

import bottle
from bottle import request, response
import sqlalchemy as sa
import sqlalchemy.orm as orm

import bauble.db as db
import bauble.i18n
from bauble.model import Organization, User
from bauble.server import app, API_ROOT, parse_accept_header, JSON_MIMETYPE, TEXT_MIMETYPE
from bauble.server.resource import Resource
import bauble.types as types
import bauble.utils as utils

# TODO: create() should return a URL that creates a new database so we
# don't accidentally destroy an existing databsae

ORG_ROOT = API_ROOT + "/organization"

class OrganizationResource(Resource):

    resource = '/organization'
    mapped_class = Organization
    relations = {
        'owners': 'handle_owners',
        'users': 'handle_users'
    }

    def handle_users(self, organization, users, session):
        for user in users:
            if 'ref' in user:
                # if this is an existing user it can't be saved if it's not
                # part of this organization
                if organization in session.new and \
                        user[organization['ref']] is not None:
                    raise ValueError("User is already in an organization")

                if organization not in session.new and \
                        user['organiation']['ref'] != organization.get_ref():
                    raise ValueError("User is not a member of this organization")

                user_id = self.get_ref_id(user.pop('ref'))
                existing = session.query(User).get(user_id)
                relations = sa.inspect(User).relationships.keys()
                for key, value in user.items():
                    if not key in relations:
                        setattr(existing, key, value)
                session.add(existing)
            else:
                new_user = User(**user)
                organization.users.append(new_user)
                if user.get('is_org_owner', False):
                    organization.owners.append(new_user)


    def handle_owners(self, organization, users, session):
        # make sure anything passed in the owners list has the
        # is_org_owner flag set
        for user in users:
            user['is_org_owner'] = True
        self.handle_users(organization, users, session)


    def __init__(self):
        super().__init__()

        # routes for organization users
        # app.route(API_ROOT + self.resource + "/<org_id>/user/<user_id>",
        #           ['OPTIONS', 'GET'], self.get_user)
        # app.route(API_ROOT + self.resource + "/<org_id>/user/<user_id>",
        #           ['OPTIONS', 'PUT'], self.save_or_update)
        # app.route(API_ROOT + self.resource + "/<org_id>/user",
        #           ['OPTIONS', 'POST'], self.save_or_update)
        # app.route(API_ROOT + self.resource + "/<resource_id>",
        #           ['OPTIONS', 'DELETE'], self.delete)


    def save_or_update(self, resource_id=None):
        response = super().save_or_update(resource_id)

        # now that the organization has been created create its schema
        # and setup the default tables
        session = this.connect()

        # create the organization database schema
        organization = session.query(Organization).get(self.get_ref_id(response))
        unique_name = "bbl_" + str(uuid.uuid4()).replace("-", "_")
        organization.pg_schema = unique_name

        # user is created without a password since we will be authenticating
        # bauble users from the "user" table althought all database
        # actions will be done by the postgresql role that owns the schema
        user_permissions = "NOSUPERUSER NOCREATEDB NOCREATEROLE " + \
            "NOCREATEUSER INHERIT LOGIN"
        session.execute("CREATE ROLE {name} WITH {perms};".\
                            format(name=unique_name, perms=user_permissions))
        session.execute("CREATE SCHEMA {name} AUTHORIZATION {name};".\
                            format(name=unique_name))
        session.commit()
        session.close()

        # now create all the default tables for the organizations schema
        tables = db.Base.metadata.sorted_tables
        for table in tables:
            table.schema = schema_name
        db.Base.metadata.create_all(session.get_bind(), tables=tables)
        session.close()

        # return the original response
        return response


    def apply_query(self, query, query_string):
        return query.filter_by(name=query_string)

    def count(self):
        bottle.abort(404)

    def count_relations(self):
        bottle.abort(404)

    def get_schema(self):
        bottle.abort(404)

    def get_relation(self):
        bottle.abort(404)



class UserResource(Resource):

    resource = '/organization/:org_id/user'
    mapped_class = User

    def get(org_id, user_id, depth=1):
        pass
