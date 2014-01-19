import bottle
from bottle import request, response
import sqlalchemy as sa
import sqlalchemy.orm as orm

import bauble.db as db
import bauble.i18n
from bauble import app, API_ROOT
from bauble.middleware import *
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

    session = None
    transaction = None;
    try:
        session = db.Session()
        connection = session.connection()
        transaction = connection.begin()
        for table in db.system_metadata.sorted_tables:
            if table.exists(connection):
                bottle.abort(409, table.name + " already exists")

        #db.system_metadata.create_all(bind=session.get_bind())
        db.system_metadata.create_all(connection)

        # NOTE: the default admin user does not have a password when the
        # database is first created
        admin_user = User(username="admin", is_sysadmin=True)
        session.add(admin_user)
        transaction.commit()
        session.commit()
        response.status = 201
    except:
        transaction.rollback()
        session.rollback()
        raise
    finally:
        if session:
            session.close()


@app.post(ADMIN_ROOT + "/import")
def import_data():
    pass


@app.post(ADMIN_ROOT + "/export/<format>")
def export_data(format="csv"):
    pass
