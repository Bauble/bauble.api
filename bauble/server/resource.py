
from collections import OrderedDict
import datetime
import inspect
import json

import bottle
from bottle import request, response
import sqlalchemy as sa
import sqlalchemy.orm as orm
import sqlalchemy.exc as sa_exc

import bauble.db as db
import bauble.error as error
import bauble.i18n
from bauble.model.family import Family, FamilySynonym, FamilyNote
from bauble.model.genus import Genus, GenusNote, GenusSynonym
from bauble.model.taxon import Taxon, TaxonSynonym, TaxonNote, VernacularName
from bauble.model.accession import Accession, AccessionNote
from bauble.model.source import Source, SourceDetail, Collection
from bauble.model.plant import Plant, PlantNote
from bauble.model.propagation import Propagation, PlantPropagation
from bauble.model.location import Location
from bauble.model.organization import Organization
from bauble.model.user import User
from bauble.model.reportdef import ReportDef
from bauble.model.lock import Lock
from bauble.server import app, API_ROOT, parse_accept_header, JSON_MIMETYPE, \
    TEXT_MIMETYPE, parse_auth_header, accept
import bauble.types as types
import bauble.utils as utils


class Resource:
    """
    """

    ignore = ['ref', 'str']
    relations = {}
    mapped_class = None
    resource = None

    # allow requests to be fullfilled without requiring the request to be
    # authorized with the user and password in the auth header
    use_auth_header = True

    def __init__(self):
        if not self.resource:
            raise NotImplementedError("resource is required")
        if not self.mapped_class:
            raise NotImplementedError("mapped_class is required")

        super().__init__()

        self.add_route(API_ROOT + self.resource,
                       {"GET": self.query,
                        "OPTIONS": self.options_response,
                        "POST": self.save_or_update,
                        })

        self.add_route(API_ROOT + self.resource + '/<resource_id>',
                       {"GET": self.get,
                        "OPTIONS": self.options_response,
                        #"POST": self.save_or_update,
                        "PUT": self.save_or_update,
                        "DELETE": self.delete
                        })

        self.add_route(API_ROOT + self.resource + "/<resource_id>/lock",
                       {"OPTIONS": self.options_response,
                        "POST": self.lock,
                        "DELETE": self.delete_lock,
                        })

        self.add_route(API_ROOT + self.resource + '/count',
                       {"GET": self.count,
                        "OPTIONS": self.options_response,
                        })

        self.add_route(API_ROOT +
                       self.resource + "/<resource_id>/<relation:path>/count",
                       {"GET": self.count_relations,
                        "OPTIONS": self.options_response,
                        })

        self.add_route(API_ROOT + self.resource + "/schema",
                       {"OPTIONS": self.options_response,
                        "GET": self.get_schema
                        })

        self.add_route(API_ROOT + self.resource + "/<relation:path>/schema",
                       {"OPTIONS": self.options_response,
                        'GET': self.get_schema
                        })

        self.add_route(API_ROOT +
                       self.resource + "/<resource_id>/<relation:path>",
                       {"OPTIONS": self.options_response,
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
                try:
                    return method_map[request.method](*args, **kwargs)
                except Exception as e:
                    print('** Error: ' + str(e))
                    raise
            else:
                bottle.abort(404)
        app.route(route, list(method_map.keys()), route_handler)


    def connect(self):
        username = password = None
        if self.use_auth_header:
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                bottle.abort(401, "No Authorization header.")
            username, password = parse_auth_header(auth_header)

            # make sure the user's organization has been approved and that the
            # organization and the user hasn't been suspended
            session = None
            try:
                session = db.connect()
                user = session.query(User).filter_by(username=username).one()
                if user.organization and not user.organization.date_approved:
                    bottle.abort(480)
                if user.organization and user.organization.date_suspended:
                    bottle.abort(481)
                if user.date_suspended:
                    bottle.abort(482)
            except orm.exc.NoResultFound:
                bottle.abort(401)
            finally:
                if session:
                    session.close()

        # validate the password
        try:
            session = db.connect(username, password)
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
        session = None
        try:
            session = self.connect()
            count = session.query(self.mapped_class).count()
            return str(count)
        finally:
            if session:
                session.close()



    @accept(TEXT_MIMETYPE)
    def count_relations(self, resource_id, relation):
        if request.method == "OPTIONS":
            return {}

        # get the mapper for the last item in the list of relations
        mapper = orm.class_mapper(self.mapped_class)
        for name in relation.split('/'):
            mapper = getattr(mapper.relationships, name).mapper

        session = None
        try:
            session = self.connect()

            # query the mapped class and the end point relation using the
            # list of the passed relations to create the join between the
            # two
            query = session.query(self.mapped_class, mapper.class_).\
                filter(getattr(self.mapped_class, 'id') == resource_id).\
                join(*relation.split('/'))

            count = query.count()
            return str(count)
        finally:
            if session:
                session.close()


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



        # get the mapper for the last item in the list of relations
        mapper = orm.class_mapper(self.mapped_class)
        for name in relation.split('/'):
            mapper = getattr(mapper.relationships, name).mapper

        session = None
        try:
            session = self.connect()
            # query the mapped class and the end point relation using the
            # list of the passed relations to create the join between the
            # two
            query = session.query(self.mapped_class, mapper.class_).\
                filter(getattr(self.mapped_class, 'id') == resource_id).\
                join(*relation.split('/'))

            response.content_type = '; '.join((JSON_MIMETYPE, "charset=utf8"))
            results = [obj.json(depth=depth) for parent, obj in query]
            return {'results': results}
        finally:
            if(session):
                session.close()


    @accept(JSON_MIMETYPE)
    def get(self, resource_id, depth=1):
        """
        Handle GET requests on this resource.

        Return a standard json response object representing the mapped_class
        where the queried objects are returned in the json object in
        the collection_name array.
        """
        if request.method == "OPTIONS":
            return {}

        session = None
        try:
            session = self.connect()
            obj = session.query(self.mapped_class).get(resource_id)

            response.content_type = '; '.join((JSON_MIMETYPE, "charset=utf8"))
            return obj.json(depth=depth)
        finally:
            session.close()


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
            elif isinstance(column.type, sa.Boolean):
                column_dict['type'] = 'boolean'
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


        # TODO: should split on either / or . to allow dot or slash delimeters
        # between references

        def get_relation_class(relation):
            # get the class at the end of the relationship
            relation_mapper = orm.class_mapper(self.mapped_class)
            for kid in relation.split('.'):
                relation_mapper = getattr(relation_mapper.relationships, kid).mapper
            return relation_mapper.class_

        session = None
        try:
            session = self.connect()
            json_objs = []
            if relations:
                # use an OrderedDict so we can maintain the default sort
                # order on the resource and
                unique_objs = OrderedDict()

                # get the json objects for each of the relations and add
                # them to the main resource json at
                # resource[relation_name], e.g. resource['genera.taxa']
                for relation in relations:
                    query = session.\
                        query(self.mapped_class, get_relation_class(relation)).\
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
            return {'results': json_objs}
        finally:
            if session:
                session.close()


    def delete(self, resource_id):
        """
        Handle DELETE requests on this resource.
        """
        session = None
        try:
            session = self.connect()
            obj = session.query(self.mapped_class).get(resource_id)
            session.delete(obj)
            session.commit()
        finally:
            if session:
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
            raise bottle.abort(415, 'Expected application/json')

        response.content_type = '; '.join((JSON_MIMETYPE, "charset=utf8"))

        # we assume all requests are in utf-8
        data = json.loads(request.body.read().decode('utf-8'))

        # remove all the JSON properties we should ignore
        for name in self.ignore:
            data.pop(name, None)

        relation_data = {}
        for name in self.relations.keys():
            if name in data:
                relation_data[name] = data.pop(name)

        session = None
        try:
            session = self.connect()
            # if this is a PUT to a specific ID then get the existing family
            # else we'll create a new one
            if request.method == 'PUT' and resource_id is not None:
                instance = session.query(self.mapped_class).get(resource_id)
                for key in data.keys():
                    setattr(instance, key, data[key])
                response.status = 200
            else:
                instance = self.mapped_class(**data)
                session.add(instance)
                response.status = 201

            # TODO: we should check for any fields that aren't defined in
            # the class or in self.relations and show an error instead
            # waiting for SQLAlchemy to catch it

            # this should only contain relations that are already in self.relations
            for name in relation_data:
                getattr(self, self.relations[name])(instance, relation_data[name],
                                                    session)
            session.commit()
            return instance.json(depth=depth)
        except sa_exc.IntegrityError as exc:
            bottle.abort(409, str(exc))
        finally:
            if session:
                session.close()


    def lock(self, resource_id):
        """
        """
        try:
            session = self.connect()
            username, password = parse_auth_header()
            user = session.query(User).filter_by(username=username).one()

            # check if a lock already exists for this resource
            resource = request.path[len(API_ROOT):-len("/lock")]
            print("search_path: ", session.bind.execute("SHOW search_path").scalar())
            is_locked = session.query(Lock).\
                filter(Lock.resource==resource, Lock.user_id==user.id,
                       Lock.date_released is not None).count() > 0
            if is_locked:
                bottle.abort(423, 'Resource is already locked')



            # lock the resource
            lock = Lock(resource=resource, user_id=user.id)
            session.add(lock)
            session.commit()
            return lock.json(depth=1)
        finally:
            if session:
                session.close()


    def delete_lock(resource_id):
        """
        """
        # delete the lock


    @staticmethod
    def get_ref_id(ref):
        # assume that if ref is not a str then it is a resource JSON object
        if not isinstance(ref, str):
            ref = ref['ref']
        return ref.split('/')[-1]


    def apply_query(self, query, query_string):
        raise bottle.abort(404, "Query on " + self.resource +" not supported")


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


    def from_json(self, json):
        # TODO: build the objects from json data....factor out the code from
        # save_or_update so that other resources can reuse the same code if
        # saving a relation resource
        pass



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
        return query.filter(Family.family.ilike(query_string))


class GenusResource(Resource):
    resource = "/genus"
    mapped_class = Genus
    relations = {
        'family': 'handle_family',
        'notes': 'handle_notes',
        'synonyms': 'handle_synonyms'
    }

    def handle_family(self, genus, family, session):
        genus.family_id = self.get_ref_id(family)

    def handle_notes(self, genus, notes, session):
        self.note_handler(genus, notes, GenusNote, session)

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
            query = session.query(GenusSynonym).filter_by(synonym_id=synonym_id)
            if(query.count() < 0):
                synonym = GenusSynonym(taxon=taxon)
                synonym.synonym_id = synonym_id

    def apply_query(self, query, query_string):
        return query.filter(Genus.genus.ilike(query_string))


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
        for vern in vernacular_names:
            if 'ref' not in vern:
                default = vern.pop('default', None)
                if isinstance(default, str):
                    default = True if vern['default'].lower() == 'true' else False
                new_vern = VernacularName(taxon=taxon, **vern)
                if default:
                    taxon.default_vernacular_name = new_vern
                session.add(new_vern)


    def handle_notes(self, taxon, notes, session):
        self.note_handler(taxon, notes, TaxonNote, session)


    def apply_query(self, query, query_string):
        mapper = orm.class_mapper(Taxon)
        ilike = lambda col: lambda val: utils.ilike(mapper.c[col], '%%%s%%' % val)
        properties = ['sp', 'sp2', 'infrasp1', 'infrasp2',
                      'infrasp3', 'infrasp4']
        ors = sa.or_(*[ilike(prop)(query) for prop in properties])
        return query.filter(ors)



class VernacularNameResource(Resource):
    resource = "/vernacularname"
    mapped_class = VernacularName



class AccessionResource(Resource):
    resource = "/accession"
    mapped_class = Accession
    ignore = ['ref', 'str', 'taxon_str']

    relations = {
        'taxon': 'handle_taxon',
        'source': 'handle_source',
        'notes': 'handle_notes',
        'verifications': 'handle_verifications',
        'vouchers': 'handle_vouchers',
    }


    def handle_verifications(self, accession, verifications, session):
        pass

    def handle_vouchers(self, accession, vouchers, session):
        pass

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
        return query.filter(Accession.code.ilike(query_string))

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
        return query.filter(Plant.code.ilike(query_string))

    def handle_notes(self, plant, notes, session):
        self.note_handler(plant, notes, PlantNote, session)


class LocationResource(Resource):
    resource = "/location"
    mapped_class = Location

    def apply_query(self, query, query_string):
        return query.filter(Location.code.ilike(query_string))


class SourceDetailResource(Resource):
    resource = "/sourcedetail"
    mapped_class = SourceDetail


class OrganizationResource(Resource):

    resource = '/organization'
    mapped_class = Organization
    ignore = ['ref', 'str', 'date_created', 'date_approved', 'data_suspended']
    relations = {
        'owners': 'handle_owners',
        'users': 'handle_users'
    }

    def __init__(self):
        # add my route before initializing the rest of the resource
        # so my route with match before the default routes
        self.add_route(API_ROOT + self.resource + "/<resource_id>/approve",
                       {'POST': self.approve,
                        'OPTIONS': self.options_response
                        })
        self.add_route(API_ROOT + self.resource + "/<resource_id>/admin",
                       {'GET': self.get_admin_data,
                        'OPTIONS': self.options_response
                        })
        super().__init__()

    def approve(self, resource_id):
        username, password = parse_auth_header()
        session = None
        try:
            session = self.connect()

            user = session.query(User).filter_by(username=username).one()
            if not user.is_sysadmin:
                bottle.abort(403, "Only a sysadmin can approve an organization.")

            org = session.query(Organization).get(resource_id)
            org.date_approved = datetime.date.today()
            session.commit()
            response = org.json()
        finally:
            if session:
                session.close()

        return response


    def get_admin_data(self, resource_id):
        username, password = parse_auth_header()
        session = None
        try:
            session = self.connect()
            user = session.query(User).filter_by(username=username).one()
            if not user.is_sysadmin:
                bottle.abort(403, "Only a sysadmin can view the organizations admin data.")
            org = session.query(Organization).get(resource_id)
        finally:
            if session:
                session.close()
        return org.admin_json()


    def handle_users(self, organization, users, session):
        for user in users:
            password = user.pop("password", None)

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
                if password:
                    existing.set_password(password)
            else:
                new_user = User(**user)
                organization.users.append(new_user)
                if user.get('is_org_owner', False):
                    organization.owners.append(new_user)
                if password:
                    new_user.set_password(password)


    def handle_owners(self, organization, users, session):
        # make sure anything passed in the owners list has the
        # is_org_owner flag set
        for user in users:
            user['is_org_owner'] = True
            user['is_org_admin'] = True
        self.handle_users(organization, users, session)


    def save_or_update(self, resource_id=None):
       # TODO: also make sure only sysadmins can create organizations otherwise
        request_user = password = None
        try:
            (request_user, password) = parse_auth_header()
        except Exception as exc:
            # The save/update an organization was not made with by an authorized
            # user which means it is a request for a new account.  This allows the
            self.use_auth_header = False

        try:
            response = super().save_or_update(resource_id)
        except sa.exc.IntegrityError:
            bottle.abort(409)

        # create the default tables for the organization
        session = None
        try:
            session = self.connect()
            organization = session.query(Organization).get(self.get_ref_id(response))
            if not organization.pg_schema:
                bottle.abort(500, "Couldn't create the organization's schema")

            tables = db.Base.metadata.sorted_tables
            for table in tables:
                table.schema = organization.pg_schema
            db.Base.metadata.create_all(session.get_bind(), tables=tables)
        finally:
            if session:
                session.close()

        # reset the schema on all tables so that future operations use the
        # search path
        for table in tables:
            table.schema = None

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
    ignore = ['ref', 'str', 'password', 'is_sysadmin', 'is_org_owner',
              'is_org_admin']

    def __init__(self):
        # add my route before initializing the rest of the resource
        # so my route with match before the default routes
        self.add_route(API_ROOT + self.resource + "/<resource_id>/password",
                       {'POST': self.set_password,
                        'OPTIONS': self.options_response
                        })
        super().__init__()


    def set_password(self, resource_id):
        """Change the password for the user making the request.
        """
        if JSON_MIMETYPE not in request.headers.get("Content-Type"):
            bottle.abort(415, 'Expected application/json')

        session = None
        try:
            session = self.connect()
            user = session.query(User).get(resource_id)

            username, password = parse_auth_header()
            if user.username != username:
                bottle.abort(403, 'Cannot change another users password')

            # we assume all requests are in utf-8
            data = json.loads(request.body.read().decode('utf-8'))
            if data.get('password', "") == "":
                bottle.abort(400, "Invalid password")

            user.set_password(data['password'])
            session.commit()
        finally:
            if session:
                session.close()


    def save_or_update(self, resource_id=None, depth=1):
        session = None
        request_user, password = parse_auth_header()
        # TODO: if this is a new user then we need to make sure a password is sent
        # in the request

        # TODO: make sure the user making this request is an admin of the
        # organization that this user is a part of
        response = super().save_or_update(resource_id, depth)

        # if this is a new user set the password
        if request.method == 'POST' and response:
            try:
                session = self.connect()
                resource_id = resource_id if resource_id else self.get_ref_id(response['ref'])
                user = session.query(User).get(resource_id)
                # we assume all requests are in utf-8
                data = json.loads(request.body.read().decode('utf-8'))
                user.set_password(data['password'])
            finally:
                if session:
                    session.close()

        return response


    def apply_query(self, query, query_string):
        return query.filter(User.username.ilike(query_string))


    def handle_organization(self, user, organization, session):
        user.organization_id = self.get_ref_id(organization)


class ReportDefResource(Resource):

    resource = '/report'
    mapped_class = ReportDef
    ignore = ['ref', 'str', 'created_by_user_id', 'last_updated_by_user_id']

    def save_or_update(self, resource_id=None, depth=1):
        session = None
        username, password = parse_auth_header()
        # TODO: if this is a new user then we need to make sure a password is sent
        # in the request

        # TODO: make sure the user making this request is an admin of the
        # organization that this user is a part of
        response = super().save_or_update(resource_id, depth)

        print('response.status', response.status)
        # update the created and last_updated users
        if response and response.status == 200:
            try:
                session = self.connect()
                resource_id = resource_id if resource_id else self.get_ref_id(response['ref'])
                report = session.query(ReportDef).get(resource_id)
                user = session.query(User).filter_by(username=username).one()
                report.last_updated_by_user = user
                report.created_by_user = report.created_by if report.created_by else user
                session.commit()
            finally:
                if session:
                    session.close()

        return response
