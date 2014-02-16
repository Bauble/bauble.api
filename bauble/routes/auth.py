from datetime import datetime, timedelta
import random
import string

import bottle
from bottle import request

import bauble.db as db
from bauble import app, API_ROOT
from bauble.middleware import basic_auth
from bauble.model import User


def create_access_token():
    rand = random.SystemRandom()
    token = ''.join([rand.choice(string.ascii_letters + string.digits) for i in range(32)])
    expiration = datetime.now() + timedelta(weeks=2)
    return token, expiration


@app.get(API_ROOT + "/login")
def login():
    auth = request.auth
    if not auth:
        bottle.abort(401, "No Authorization header.")
    username, password = auth
    session = db.Session()
    try:
        user = session.query(User).filter_by(email=username).first()
        if not user or not user.password == password:
            bottle.abort(401)  # not authorized

        user.access_token, user.access_token_expiration = create_access_token()
        user.last_accesseed = datetime.now()
        session.commit()
        user_json = user.json()
    finally:
        session.close()

    return user_json


@app.get(API_ROOT + "/logout")
@basic_auth
def logout():
    request.user.access_token = None
    request.user.access_token_expiration = None
    request.session.commit()
