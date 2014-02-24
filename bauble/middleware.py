
import datetime
import json

import bcrypt
import bottle
from bottle import request, response

import bauble.db as db
from bauble.model import User
from bauble.server import parse_accept_header
import bauble.utils as utils

# TODO: maybe we should just close the session in each middleware function
# and if the

def basic_auth(next):
    """Route handler decorator that authorizes the user using Basic Auth.  This
    method attaches a 'user' attribute to the request that represents the
    authorized user.  It attaches a 'session' attribute who schema uses the
    organizational schema for the user and should be used by all future
    requests.

    """

    def _wrapped(*args, **kwargs):
        auth = request.auth
        if not auth:
            bottle.abort(401, "No Authorization header.")

        email, password = auth
        request.session = db.Session()
        request.user = request.session.query(User).filter_by(email=email).first()
        if not request.user or not password:
            bottle.abort(401)  # not authorized

        # *************
        # TODO: make sure we have passed the access_token_expiration
        # *************

        # basic_auth authorizes agains the users access token rather than the password
        # only /login uses the password
        if request.user.access_token == password:
            tmp_session = db.Session()
            try:
                # update the last accessed column in a separate session so we
                # don't dirty our request session and inadvertantly commit something
                tmp_user = tmp_session.query(User).get(request.user.id)
                tmp_user.last_accesseed = datetime.datetime.now()
                tmp_session.commit()

                # make sure the request.user picks up the last_accessed
                # property in case its accessed
                request.session.expire(request.user)
            finally:
                tmp_session.close()
        else:
            bottle.abort(401)

        # if not request.user.is_sysadmin and not request.user.organization:
        #     bottle.abort(401, "User does not belong to an organization")

        # should only get here if the user either has an organization or the user is a
        # sysadmin
        if request.user.organization:
            db.set_session_schema(request.session, request.user.organization.pg_schema)

        # make sure the session is always closed before we return
        try:
            content = next(*args, **kwargs)
        except:
            raise
        finally:
            request.session.close()

        return content

    return _wrapped


def with_session(next):

    def _wrapped(*args, **kwargs):
        request.session = db.Session()
        if hasattr(request, 'user') and request.user:
            db.set_session_schema(session, request.user.organization.pg_schema)
        # close the session before we return the content
        content = next(*args, **kwargs)
        request.session.close()
        return content
    return _wrapped



def accept(mimetype):
    def _decorator(next):
        def _wrapped(*args, **kwargs):
            accepted = parse_accept_header()
            if mimetype not in accepted and '*/*' not in accepted:
                bottle.abort(406, 'Expected application/json')
            request.accept = accepted
            return next(*args, **kwargs)
        return _wrapped

    return _decorator


def resolve_relation(column, relation, required=True):
    """
    Resolve a relationship for column.
    """
    def _decorator(next):
        def _wrapped(*args, **kwargs):
            # if there isn't a column_id value look it up in the relation field
            if not column in request.json:
                if isinstance(request.json[relation], dict):
                    # resolve from json dict
                    request.json[column] = request.json[relation]['id']
                else:
                    # resolve from the route, e.g. /taxon/1234
                    request.json[column] = utils.get_ref_id(request.json[relation])

            if required and not column in request.json and not request.json[column]:
                bottle.abort(401, "Could not resovle relation {0} for column {1}".format(relation, column))
            return next(*args, **kwargs)
        return _wrapped
    return _decorator




class accept2:
    """Decorator class to handle parsing the HTTP Accept header.
    """

    def __init__(self, mimetype):
        self.mimetype = mimetype


    def __call__(self, next):
        def inner(*args, **kwargs):
            accepted = parse_accept_header()

            def set_depth(mimetype):
                if 'depth' not in accepted[mimetype]:
                    return
                nonlocal args

                # insert the depth into the argument list
                try:
                    depth = int(accepted[mimetype]['depth'])
                except Exception as exc:
                    bottle.abort(400,"Invalid depth value")

                argspec = inspect.getfullargspec(next)[0]

                # kwargs['depth'] = depth
                if 'depth' in argspec and 'depth' not in kwargs:
                    index = argspec.index('depth')
                    if args and len(args) > index and args[index] is not None:
                        new_args = list(args)
                        new_args[index] = depth
                        args = tuple(new_args)
                    else:
                        kwargs['depth'] = depth
                else:
                    kwargs['depth'] = depth

            if self.mimetype in accepted:
                set_depth(self.mimetype)
            elif '*/*' in accepted:
                set_depth('*/*')
            else:
                bottle.abort(406, 'Expected application/json')
            return next(*args, **kwargs)
        return inner


def filter_param(mapped_class, columns):
    def _decorator(next):
        def _wrapped(*args, **kwargs):
            request.filter = None
            if 'filter' in request.query:
                query = request.session.query(mapped_class)
                filter_json = json.loads(request.query.filter)
                filter_by = {key: value for (key, value) in filter_json.items()
                             if key in columns}
                for col, value in filter_by.items():
                    print(col, ", ", value)
                    query = query.filter(getattr(mapped_class, col).ilike(value))

                request.filter = query
            return next(*args, **kwargs)
        return _wrapped
    return _decorator
