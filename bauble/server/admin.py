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
DB_NAME=db.db_url_template.split('/')[-1] 

@app.post(ADMIN_ROOT + "/initdb")
def initdb():
    auth_header = request.headers['Authorization']
    user, password = bottle.parse_auth(auth_header)
    db_url = "postgresql://{user}:{password}@localhost/postgres"\
        .format(user=user, password=password)
    engine = sa.create_engine(db_url)
    conn = engine.connect()
    
    # check if database already exists
    result = conn.execute("SELECT 1 from pg_database where datname='{dbname}'"\
        .format(dbname=DB_NAME))
    if result.first() == 1:
        bottle.abort("409", "Database already exists")
    
    # create the database
    conn.execute('commit')  # commit implicit transaction
    conn.execute("create database {dbname};".format(dbname=DB_NAME))
    conn.close()
    
    # connect with out session and setup the default tables
    import bauble.model as model
    session = db.connect(user, password)
    table = sa.inspect(model.User).local_table
    table.create(session.get_bind())
    session.close()
