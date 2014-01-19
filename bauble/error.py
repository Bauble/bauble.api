#
# all bauble exceptions and errors
#

import bottle
from bottle import request
from bauble import app



class BaubleError(Exception):
    def __init__(self, msg=None):
        self.msg = msg
    def __str__(self):
        if self.msg is None:
            return str(type(self).__name__)
        else:
            return '%s: %s' % (type(self).__name__, self.msg)
        return self.msg

class CommitException(Exception):

    def __init__(self, exc, row):
        self.row = row # the model we were trying to commit
        self.exc = exc # the exception thrown while committing

    def __str__(self):
        return str(self.exc)


class PermissionError(BaubleError):
    pass

class AuthenticationError(BaubleError):
    pass

class LoginError(BaubleError):
    pass

class DatabaseError(BaubleError):
    pass

class EmptyDatabaseError(DatabaseError):
    pass

class MetaTableError(DatabaseError):
    pass

class TimestampError(DatabaseError):
    pass

class RegistryError(DatabaseError):
    pass

class VersionError(DatabaseError):

    def __init__(self, version):
        super(VersionError, self).__init__()
        self.version = version


class SQLAlchemyVersionError(BaubleError):
    pass

class CheckConditionError(BaubleError):
    pass



def check(condition, msg=None):
    """
    Check that condition is true.  If not then raise
    CheckConditionError(msg)
    """
    if not condition:
        raise CheckConditionError(msg)


@app.error(500)
def default_error_handler(error):
    # TODO: only print the error when the debug flag is set
    # make sure the error is printed in the log
    from bauble.routes import enable_cors
    enable_cors()
    if isinstance(error, str):
        return error
    elif error.body:
        return str(error.body)
    elif error.exception:
        return str(error.exception)


common_errors = [400, 403, 404, 406, 409, 415, 500]
for code in common_errors:
    app.error(code)(default_error_handler)

@app.error(401)
def error_handler_401(error):
    from bauble.routes import enable_cors
    enable_cors()
    header = request.headers.get('Authorization', None)
    if header:
        user, password = bottle.parse_auth(header)
        return "Could not authorize user: {user}".format(user=user)
    else:
        return "No Authorization header."



#
# 480 and up are custom response codes
#
# TODO: ** i'm not sure about these custom response codes anymore
@app.error(480)
def error_handler_480(error):
    return default_error_handler("Account has not been approved")

@app.error(481)
def error_handler_481(error):
    return default_error_handler("Organization account has been suspended")

@app.error(482)
def error_handler_482(error):
    return default_error_handler("User account has been suspended")
