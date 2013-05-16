import json
import uuid

import bottle
from bottle import request, response
import sqlalchemy as sa
import sqlalchemy.orm as orm

import bauble.db as db
import bauble.i18n
import bauble.model.organization as org
from bauble.server import app, API_ROOT, parse_accept_header, JSON_MIMETYPE, TEXT_MIMETYPE
from bauble.server.resource import Resource
import bauble.types as types
import bauble.utils as utils

# TODO: create() should return a URL that creates a new database so we
# don't accidentally destroy and existing databsae

ORG_ROOT = API_ROOT + "/organization"
DB_NAME=db.db_url_template.split('/')[-1]


class OrganizationResource(Resource):

    resource = '/organization'
    mapped_class = org.Organization

    def save_or_update(self, resource_id=None):
        response = super().save_or_update(resource_id)

        # now that the organization has been created create its schema
        # and setup the default tables
        auth_header = request.headers['Authorization']
        user, password = bottle.parse_auth(auth_header)
        session = db.connect(user, password)

        # TODO: maybe we should create a database level user for each organization
        # that can own the schema

        # create the organization database schema
        organization = session.query(org.Organization).get(self.get_ref_id(response))
        schema_name = "bbl_" + str(uuid.uuid4()).replace("-", "_")
        organization.pg_schema = schema_name
        session.execute("CREATE SCHEMA {name};".format(name=schema_name))
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
