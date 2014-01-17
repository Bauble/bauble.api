
import datetime

import bcrypt
import bottle
from bottle import request, response

import bauble.db as db
from bauble.model import User
from bauble.server import parse_accept_header

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
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            bottle.abort(401, "No Authorization header.")

        username, password = bottle.request.auth
        request.session = db.Session()
        request.user = request.session.query(User).filter_by(username=username).first()
        if not request.user:
            bottle.abort(401) # not authorized

        encode = lambda s: s.encode("utf-8") if s else "".encode("utf-8")
        if request.user and (request.user.password and password) and bcrypt.hashpw(encode(password), encode(request.user.password)) == encode(request.user.password):
            try:
                # update the last accessed column in a separate session so we
                # don't dirty our request session
                tmp_session = db.Session();
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
