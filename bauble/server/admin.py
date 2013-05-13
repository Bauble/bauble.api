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
    session = db.connect(user=user, password=password, schema='public')
    bind = session.get_bind()
    conn = bind.connect()
    
    
    # check if database already exists
    sql = "SELECT 1 from pg_database WHERE datname='{dbname}';".\
        format(dbname=DB_NAME)
    value = conn.execute(sql)
    print('value: ', value)
    if values == '1':
        abort("500", "Database already exists")

    # create the database
    conn.execute("create database {dbname}", dbname=DB_NAME)
    
    # we just need to create the initial system level database, not 
    # a user/organization databse
    import bauble.mode.user as user
    user.User.create(session.get_bind())


    
    
    
