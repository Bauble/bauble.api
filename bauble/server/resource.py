from collections import OrderedDict

import json
import os
import uuid

import bottle
from bottle import request, response
import sqlalchemy as sa
import sqlalchemy.orm as orm

import bauble.db as db
import bauble.error as error
import bauble.i18n
from bauble.model.family import Family, FamilySynonym, FamilyNote
from bauble.model.genus import Genus, GenusNote
from bauble.model.taxon import Taxon, TaxonSynonym, TaxonNote
from bauble.model.accession import Accession, AccessionNote
from bauble.model.source import Source, SourceDetail, Collection
from bauble.model.plant import Plant, PlantNote
from bauble.model.propagation import Propagation, PlantPropagation
from bauble.model.location import Location
from bauble.model.organization import Organization
from bauble.model.user import User
from bauble.server import app, API_ROOT, parse_accept_header, JSON_MIMETYPE, TEXT_MIMETYPE, enable_cors
import bauble.types as types
import bauble.utils as utils


class accept:
    """Decorator class to handle parsing the HTTP Accept header.
    """

    def __init__(self, mimetype):
        self.mimetype = mimetype


    def __call__(self, func):
        def inner(*args, **kwargs):
            accepted = parse_accept_header()

            def set_depth(mimetype):
                if 'depth' in accepted[mimetype]:
                    kwargs['depth'] = int(accepted[self.mimetype]['depth'])

            if self.mimetype in accepted:
                set_depth(self.mimetype)
            elif '*/*' in accepted:
                set_depth('*/*')
            else:
                bottle.abort(406, 'Expected application/json')
                # raise bottle.HTTPError('406 Not Accepted',
                #                        'Expected application/json')

            return func(*args, **kwargs)
        return inner

# TODO: should probably rename this to connect_as_user and on success
# add a session parameter to the wrapped method

class auth_user:
    """Decorator class to authorize the current request against the user table.
    """

    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        def inner(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                bottle.abort(401, "No Authorization header.")
            username, password = parse_auth_header()
            session = db.get_session()
            user = db.authenticate(username, password)
            session.close()
            if not user:
                bottle.abort(401)
            if user.id != resource_id and not user.is_sysadmin:
                # don't allow change other users data
                bottle.abort(403)
            return func(*args, **kwargs)
        return inner


def parse_auth_header(header=None):
    """Parse the and return a (user, password) tuple.  If not header is passed
    then use the header from the current request.
    """
    if not header:
        header = request.headers.get('Authorization')
    return  bottle.parse_auth(header)



class Resource:
    """
    """

    ignore = ['ref', 'str']
    relations = {}
    mapped_class = None
    resource = None

    def __init__(self):
        if not self.resource:
            raise NotImplementedError("resource is required")
        if not self.mapped_class:
            raise NotImplementedError("mapped_class is required")

        super().__init__()

        self.add_route(API_ROOT + self.resource, {
                "GET": self.query,
                "OPTIONS": self.options_response,
                "PUT": self.save_or_update,
                })

        self.add_route(API_ROOT + self.resource + '/<resource_id>', {
                "GET": self.get,
                "OPTIONS": self.options_response,
                "POST": self.save_or_update,
                "PUT": self.save_or_update,
                "DELETE": self.delete
                })

        self.add_route(API_ROOT + self.resource + '/count', {
                "GET": self.count,
                "OPTIONS": self.options_response,
                })

        self.add_route(API_ROOT +
                       self.resource +"/<resource_id>/<relation:path>/count", {
                "GET": self.count_relations,
                "OPTIONS": self.options_response,
                })

        self.add_route(API_ROOT + self.resource + "/schema", {
                "OPTIONS": self.options_response,
                "GET": self.get_schema
                })
        self.add_route(API_ROOT + self.resource + "/<relation:path>/schema", {
                "OPTIONS": self.options_response,
                'GET': self.get_schema
                })
        self.add_route(API_ROOT +
                       self.resource + "/<resource_id>/<relation:path>", {
                "OPTIONS": self.options_response,
                "GET": self.get_relation
                })

    session_events = []


    def options_response(self, *args, **kwargs):
        pass


    def add_route(self, route, method_map):
        """Add route that supports multiple methods on the same
        resource location.
        """
        def route_handler(*args, **kwargs):
            if request.method in method_map:
                return method_map[request.method](*args, **kwargs)
            else:
                abort(404)
        app.route(route, list(method_map.keys()), route_handler)


    def connect(self):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            bottle.abort(401, "No Authorization header.")
        user, password = parse_auth_header(auth_header)

        # validate the password
        try:
            session = db.connect(user, password)
        except error.AuthenticationError as exc:
            bottle.abort(401)

        # connect any session event listeners
        for event, callback in self.session_events:
            sa.event.list(session, event, callback)

        return session


    @accept(TEXT_MIMETYPE)
    def count(self, resource_id):
        if request.method == "OPTIONS":
            return {}

        session = self.connect();

        count = session.query(self.mapped_class).count()
        session.close()
        return str(count)


    @accept(TEXT_MIMETYPE)
    def count_relations(self, resource_id, relation):
        if request.method == "OPTIONS":
            return {}

        session = self.connect()

        # get the mapper for the last item in the list of relations
        mapper = orm.class_mapper(self.mapped_class)
        for name in relation.split('/'):
            mapper = getattr(mapper.relationships, name).mapper

        # query the mapped class and the end point relation using the
        # list of the passed relations to create the join between the
        # two
        query = session.query(self.mapped_class, mapper.class_).\
            filter(getattr(self.mapped_class, 'id') == resource_id).\
            join(*relation.split('/'))

        count = query.count()
        session.close()
        return str(count)


    @accept(JSON_MIMETYPE)
    def get_relation(self, resource_id, relation, depth=1):
        """
        Handle GET requests on relation rooted at this resource.

        Return a JSON object where the results property represents the items
        from the relation end point.  e.g. /family/1/genera/taxa would return
        all the taxa related to the family with id=1.
        """
        if request.method == "OPTIONS":
            return {}

        session = self.connect()

        # get the mapper for the last item in the list of relations
        mapper = orm.class_mapper(self.mapped_class)
        for name in relation.split('/'):
            mapper = getattr(mapper.relationships, name).mapper

        # query the mapped class and the end point relation using the
        # list of the passed relations to create the join between the
        # two
        query = session.query(self.mapped_class, mapper.class_).\
            filter(getattr(self.mapped_class, 'id') == resource_id).\
            join(*relation.split('/'))

        response.content_type = '; '.join((JSON_MIMETYPE, "charset=utf8"))
        results = [obj.json(depth=depth) for parent, obj in query]
        response_json = {'results': results}
        session.close()
        return response_json


    @accept(JSON_MIMETYPE)
    def get(self, resource_id, session=None, depth=1):
        """
        Handle GET requests on this resource.

        Return a standard json response object representing the mapped_class
        where the queried objects are returned in the json object in
        the collection_name array.
        """
        if request.method == "OPTIONS":
            return {}

        session = self.connect()
        obj = session.query(self.mapped_class).get(resource_id)

        response.content_type = '; '.join((JSON_MIMETYPE, "charset=utf8"))
        response_json = obj.json(depth=depth)
        session.close()
        return response_json


    def get_schema(self, relation=None):
        """
        Return a JSON representation of the queryable schema of this
        resource or one of it's relations.

        This doesn't necessarily represent the json object that is returned
        for this resource.  It is more for the queryable parts of this resources
        to be used for building reports and query strings.

        A schema object can be declared in the class or else a schema
        will be generated from the mapper.  If a schema is not to be
        returned then set schema to None.
        """
        flags = request.query.flags
        if(flags):
            flags = flags.split(',')

        mapper = orm.class_mapper(self.mapped_class)
        if relation:
            for name in relation.split('/'):
                mapper = getattr(mapper.relationships, name).mapper
        schema = dict(columns={}, relations={})

        for name, column in mapper.columns.items():
            if name.startswith('_'):
                continue
            column_dict = dict(required=column.nullable)
            schema['columns'][name] = column_dict
            if isinstance(column.type, sa.String):
                column_dict['type'] = 'string'
                column_dict['length'] = column.type.length
            elif isinstance(column.type, sa.Integer):
                column_dict['type'] = 'int'
            elif isinstance(column.type, types.Enum):
                column_dict['type'] = 'list'
                column_dict['values'] = column.type.values
            elif isinstance(column.type, types.DateTime):
                column_dict['type'] = 'datetime'
            elif isinstance(column.type, types.Date):
                column_dict['type'] = 'date'
            else:
                raise Exception("Unknown type %s for column %s: " % (str(column.type), column.name))

        if 'scalars_only' in flags:
            schema['relations'] = [key for key, rel in mapper.relationships.items() if not key.startswith('_') and not rel.uselist]
        else:
            schema['relations'] = [key for key in mapper.relationships.keys() if not key.startswith('_')]

        return schema


    @accept(JSON_MIMETYPE)
    def query(self, depth=1):
        """
        Handle GET /resource?q= requests on this resource.
        """
        q = request.query.q
        relations = request.query.relations
        if(relations):
            relations = [relation.strip() for relation in relations.split(',')]
        else:
            relations = []

        session = self.connect()

        # TODO: should split on either / or . to allow dot or slash delimeters
        # between references

        def get_relation_class(relation):
            # get the class at the end of the relationship
            relation_mapper = orm.class_mapper(self.mapped_class)
            for kid in relation.split('.'):
                relation_mapper = getattr(relation_mapper.relationships, kid).mapper
            return relation_mapper.class_

        json_objs = []
        if relations:
            # use an OrderedDict so we can maintain the default sort
            # order on the resource and
            unique_objs = OrderedDict()

            # get the json objects for each of the relations and add
            # them to the main resource json at
            # resource[relation_name], e.g. resource['genera.taxa']
            for relation in relations:
                query = session.query(self.mapped_class, get_relation_class(relation)).\
                    join(*relation.split('.'))
                if(q):
                    query = self.apply_query(query, q)

                for result in query:
                    resource = result[0]

                    # add the resource_json to unique_objs if it
                    # doesn't already exist
                    if resource.id not in unique_objs:
                        resource_json = resource.json(depth)
                        resource_json[relation] = []
                        unique_objs[resource.id] = resource_json
                    else:
                        resource_json = unique_objs[resource.id]

                    resource_json[relation].append(result[1].json(depth=depth))

            # create a list of json objs that should maintain the
            json_objs = [obj for obj in unique_objs.values()]

        else:
            query = session.query(self.mapped_class)
            if(q):
                query = self.apply_query(query, q)
            json_objs = [obj.json(depth) for obj in query]

        session.close()
        response_json = {'results': json_objs}
        response.content_type = '; '.join((JSON_MIMETYPE, "charset=utf8"))
        return response_json


    def delete(self, resource_id):
        """
        Handle DELETE requests on this resource.
        """
        session = self.connect()

        obj = session.query(self.mapped_class).get(resource_id)
        session.delete(obj)
        session.commit()
        session.close()


    @accept(JSON_MIMETYPE)
    def save_or_update(self, resource_id=None, depth=1):
        """
        Handle POST and PUT requests on this resource.

        If a family_id is passed the family will be updated. Otherwise
        it will be created.  The request body should contain a Family
        json object.

        A JSON object that represents the created Family will be
        returned in the response.
        """
        # make sure the content is JSON
        if JSON_MIMETYPE not in request.headers.get("Content-Type"):
            raise bottle.HTTPError('415 Unsupported Media Type',
                                   'Expected application/json')

        response.content_type = '; '.join((JSON_MIMETYPE, "charset=utf8"))

        session = self.connect()

        # we assume all requests are in utf-8
        data = json.loads(request.body.read().decode('utf-8'))

        # remove all the JSON properties we should ignore
        for name in self.ignore:
            data.pop(name, None)

        relation_data = {}
        for name in self.relations.keys():
            if name in data:
                relation_data[name] = data.pop(name)

        # if this is a PUT to a specific ID then get the existing family
        # else we'll create a new one
        if request.method == 'PUT' and resource_id is not None:
            instance = session.query(self.mapped_class).get(resource_id)
            for key in data.keys():
                setattr(instance, key, data[key])
            response.status = 200
        else:
            instance = self.mapped_class(**data)
            response.status = 201

        # TODO: we should check for any fields that aren't defined in
        # the class or in self.relations and show an error instead
        # waiting for SQLAlchemy to catch it

        # this should only contain relations that are already in self.relations
        for name in relation_data:
            getattr(self, self.relations[name])(instance, relation_data[name],
                                                session)

        session.add(instance)
        session.commit()
        response_json = instance.json(depth=depth)
        session.close()
        return response_json


    @staticmethod
    def get_ref_id(ref):
        # assume that if ref is not a str then it is a resource JSON object
        if not isinstance(ref, str):
            ref = ref['ref']
        return ref.split('/')[-1]


    def apply_query(self, query, query_string):
        raise bottle.HTTPError("404 Not Found", "Query on " + self.resource +
                               " not supported")


    @classmethod
    def note_handler(self, obj, notes, note_class, session):
        for note in notes:
            if 'ref'in note:
                note_id = self.get_ref_id(note.pop('ref'))
                existing = session.query(note_class).get(note_id)
                relations = sa.inspect(note_class).relationships.keys()
                for key, value in note.items():
                    if not key in relations:
                        setattr(existing, key, value)
                session.add(existing)
            else:
                obj_note = note_class(**note)
                obj.notes.append(obj_note)



class FamilyResource(Resource):

    resource = '/family'
    mapped_class = Family
    relations = {
        'notes': 'handle_notes',
        'synonyms': 'handle_synonyms'
    }

    def handle_synonyms(self, family, synonyms, session):
        # synonyms can be a list of family objects or a list of family refs
        for syn in synonyms:
            if isinstance(syn, str):
                synonym_id = self.get_ref_id(syn)
            elif isinstance(syn, dict):
                synonym_id = self.get_ref_id(syn['ref'])
            else:
                raise Exception("Synonym in unsupported format")

            # make sure this synonym doesn't already have this id since
            # we can't have dupliation ids
            query = session.query(FamilySynonym).filter_by(synonym_id=synonym_id)
            if(query.count() < 0):
                synonym = FamilySynonym(family=family)
                synonym.synonym_id = synonym_id


    def handle_notes(self, family, notes, session):
        self.note_handler(family, notes, FamilyNote, session)


    def apply_query(self, query, query_string):
        return query.filter(Family.family.like(query_string))


class GenusResource(Resource):
    resource = "/genus"
    mapped_class = Genus
    relations = {
        'family': 'handle_family',
        'notes': 'handle_notes'
    }

    def handle_family(self, genus, family, session):
        genus.family_id = self.get_ref_id(family)

    def handle_notes(self, genus, notes, session):
        self.note_handler(genus, notes, GenusNote, session)

    def apply_query(self, query, query_string):
        return query.filter(Genus.genus.like(query_string))


class TaxonResource(Resource):
    resource = "/taxon"
    mapped_class = Taxon
    relations = {
        'genus': 'handle_genus',
        'notes': 'handle_notes',
        'vernacular_names': 'handle_vernacular_names',
        'synonyms': 'handle_synonyms'
    }

    def handle_synonyms(self, taxon, synonyms, session):
        # synonyms can be a list of taxon objects or a list of taxon refs
        for syn in synonyms:
            if isinstance(syn, str):
                synonym_id = self.get_ref_id(syn)
            elif isinstance(syn, dict):
                synonym_id = self.get_ref_id(syn['ref'])
            else:
                raise Exception("Synonym in unsupported format")

            # make sure this synonym doesn't already have this id since
            # we can't have dupliation ids
            query = session.query(TaxonSynonym).filter_by(synonym_id=synonym_id)
            if(query.count() < 0):
                synonym = TaxonSynonym(taxon=taxon)
                synonym.synonym_id = synonym_id


    def handle_genus(self, taxon, genus, session):
        taxon.genus_id = self.get_ref_id(genus)


    def handle_vernacular_names(self, taxon, vernacular_names, session):
        pass

    def handle_notes(self, taxon, notes, session):
        self.note_handler(taxon, notes, TaxonNote, session)


    def apply_query(self, query, query_string):
        mapper = orm.class_mapper(Taxon)
        ilike = lambda col: lambda val: utils.ilike(mapper.c[col], '%%%s%%' % val)
        properties = ['sp', 'sp2', 'infrasp1', 'infrasp2',
                      'infrasp3', 'infrasp4']
        ors = sa.or_(*[ilike(prop)(query) for prop in properties])
        return query.filter(ors)



class AccessionResource(Resource):
    resource = "/accession"
    mapped_class = Accession

    relations = {
        'taxon': 'handle_taxon',
        'source': 'handle_source',
        'notes': 'handle_notes'
    }


    def handle_source(self, accession, source, session):
        accession.source = Source()
        if 'source_detail' in source:
            accession.source.source_detaild_id = self.get_ref_id(source['source_detail'])

        if 'collection' in source:
            accession.source.collection = Collection(**source['collection'])

        if 'propagation' in source:
            propagation = source['propagation']
            details = propagation.pop('details')
            accession.source.propagation = Propagation(**source['propagation'])
            accession.source.propagation.details = details

        if 'plant_propagation' in source:
            plant_propagation = source['plant_propagation']
            propagation = plant_propagation.pop('propagation')
            details = propagation.pop('details')
            accession.source.plant_propagation = PlantPropagation(**plant_propagation)
            accession.source.plant_propagation.propagation = Propagation(**propagation)
            accession.source.plant_propagation.propagation.details = details


    def handle_taxon(self, accession, taxon, session):
        accession.taxon_id = self.get_ref_id(taxon)


    def apply_query(self, query, query_string):
        return query.filter(Accession.code.like(query_string))

    def handle_notes(self, accession, notes, session):
        self.note_handler(accession, notes, AccessionNote, session)


class PlantResource(Resource):
    resource = "/plant"
    mapped_class = Plant

    relations = {
        'accession': 'handle_accession',
        'location': 'handle_location',
        'notes': 'handle_notes',
        'change': 'handle_change'
    }

    def handle_changel(self, plant, change, session):
        pass

    def handle_accession(self, plant, accession, session):
        plant.accession_id = self.get_ref_id(accession)

    def handle_location(self, plant, location, session):
        plant.location_id = self.get_ref_id(location)

    def apply_query(self, query, query_string):
        # TODO: we also need to support searching will full accession.plant
        # strings like the PlantSearch mapper strategy from bauble 1
        return query.filter(Plant.code.like(query_string))

    def handle_notes(self, plant, notes, session):
        self.note_handler(plant, notes, AccessionNote, session)


class LocationResource(Resource):
    resource = "/location"
    mapped_class = Location

    def apply_query(self, query, query_string):
        return query.filter(Location.code.like(query_string))


class SourceDetailResource(Resource):
    resource = "/sourcedetail"
    mapped_class = SourceDetail


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


    # TODO: only sysadmins should be able to create other sysadmins, all other
    # users should be created at /organization/<resource_id>/user
    def save_or_update(self, resource_id=None):
        response = super().save_or_update(resource_id)

        # now that the organization has been created create its schema
        # and setup the default tables
        session = self.connect()

        # create the organization datAbase schema
        organization = session.query(Organization).get(self.get_ref_id(response))
        unique_name = "bbl_" + str(uuid.uuid4()).replace("-", "_")
        organization.pg_schema = unique_name

        # user is created without a password since we will be authenticating
        # bauble users from the "user" table althought all database
        # actions will be done by the postgresql role that owns the schema
        user_permissions = "NOSUPERUSER NOCREATEDB NOCREATEROLE NOLOGIN INHERIT"
        session.execute("CREATE ROLE {name} {perms};".\
                            format(name=unique_name, perms=user_permissions))
        session.execute("CREATE SCHEMA {name} AUTHORIZATION {name};".\
                            format(name=unique_name))
        session.commit()
        session.close()

        # now create all the default tables for the organizations schema
        tables = db.Base.metadata.sorted_tables
        for table in tables:
            table.schema = unique_name
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

    resource = '/user'
    mapped_class = User
    relations = {
        'organization': 'handle_organization'
    }

    def __init__(self):
        super().__init__()

        self.add_route(API_ROOT + self.resource + "/<resource_id>/password", {
                'POST': self.set_password,
                'OPTIONS': self.options_response
                })

    def save_or_update(self, resource_id=None, depth=1):
        session = self.connect()
        request_user, password = parse_auth_header()

        # TODO: make sure the user making this request is an admin of the
        # organization that this user is a part of
        super().save_or_update(self, resource_id, depth)


    def apply_query(self, query, query_string):
        return query.filter(User.username.ilike(query_string))


    def handle_organization(self, user, organization, session):
        user.organization_id = org_id = self.get_ref_id(organization)


    @auth_user
    def set_password(self, user_id):
        pass
