import json

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
    
