import bottle
from bottle import request, response
import sqlalchemy as sa
import sqlalchemy.orm as orm

import bauble.db as db
import bauble.i18n
from bauble.server import app, API_ROOT, parse_accept_header, JSON_MIMETYPE, TEXT_MIMETYPE
import bauble.types as types
import bauble.utils as utils

# TODO: create() should return a URL that creates a new database so we
# don't accidentally destroy and existing databsae

ADMIN_ROOT = API_ROOT + "/admin"
#DB_NAME=db.db_url_template.split('/')[-1]

@app.post(ADMIN_ROOT + "/initdb")
def initdb():
    """
    Create the default databases tables and admin user. This request doesn't
    do any authentication because it can only be run on an empty database.
    """
    # setup the default tables
    from bauble.model import User, Organization
    session = db.connect()
    bind = session.get_bind()

    for table in db.system_metadata.sorted_tables:
        if table.exists(bind):
            bottle.abort(409, table.name + " already exists")

    db.system_metadata.create_all(bind=session.get_bind())

    # NOTE: the default admin user does not have a password when the
    # database is first created
    admin_user = User(username="admin", is_sysadmin=True)
    session.add(admin_user)
    session.commit()
    session.close()

    response.status = 201
