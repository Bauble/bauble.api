"""
All routes in Bauble use HTTP basic auth.
"""

from datetime import datetime, timedelta
import os
import smtplib

import bottle
from bottle import request
import sqlalchemy as sa

import bauble
import bauble.config as config
import bauble.db as db
import bauble.email as email
from bauble import app, API_ROOT
from bauble.middleware import basic_auth
from bauble.model import User
from bauble.utils import create_unique_token


def create_access_token():
    return create_unique_token(), datetime.now() + timedelta(weeks=2)


def create_password_reset_token():
    return create_unique_token(), datetime.now() + timedelta(days=1)


@app.get(API_ROOT + "/login")
def login():
    auth = request.auth
    if not auth:
        bottle.abort(401, "No Authorization header.")
    username, password = auth
    session = db.Session()
    try:
        user = session.query(User).filter(sa.func.lower(User.email) == username.lower()).first()
        if not user or not user.password == password:
            bottle.abort(401)  # not authorized

        user.access_token, user.access_token_expiration = create_access_token()
        user.last_accessed = datetime.now()
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


@app.post(API_ROOT + "/forgot-password")
def forgot_password():

    user_email = request.params.get('email', None)
    if not user_email and not user_email.contains('@'):
        bottle.abort("Valid email address required")

    session = None
    try:
        session = db.Session()
        user = session.query(User)\
                      .filter(sa.func.lower(User.email) == user_email.lower())\
                      .first()
        if not user:
            bottle.abort(422, "Could not get a user with the requested email address")
        token, expiration = create_password_reset_token()
        user.password_reset_token = token
        user.password_reset_token_expiration = expiration
        session.commit()
    finally:
        if session:
            session.close()

    app_url = config.get("BAUBLE_APP_URL")
    mappings = {'token': token, 'email': user_email, 'app_url': app_url}

    try:
        email.send_template('reset_password.txt', mappings, **{
            'to': user_email,
            'from': 'no-reply@bauble.io',
            'subject': 'Bauble Password Reset'})

    except smtplib.SMTPException as exc:
        print(exc)
        bottle.abort(500, 'Could not send reset password email.')


@app.post(API_ROOT + "/reset-password")
def reset_password():
    session = None

    user_email = request.json['email']
    try:
        session = db.Session()
        user = session.query(User).filter(sa.func.lower(User.email) == user_email.lower()).first()

        if user is None:
            print('use is None')
            # TODO: is this the correct status code?
            bottle.abort(422, 'A user could be be found with the provided email')

        if request.json['token'] != user.password_reset_token or \
           (request.json['token'] == user.password_reset_token and user.password_reset_token_expiration < datetime.now()):
            # TODO: is this the correct status code?
            bottle.abort(422, 'Invalid password reset token')

        # TODO: need to set the expiration
        user.password_reset_token = None
        user.password_reset_token_expiration = None
        user.password = request.json['password']
        user.access_token, user.access_token_expiration = create_access_token()
        user.last_accesseed = datetime.now()
        session.commit()
        user_json = user.json()

    # except Exception as exc:
    #     print('type(exc): ', type(exc))
    #     print(exc)
    #     bottle.abort(400, "Could not get a user with the requested email address")
    finally:
        if session:
            session.close()

    return user_json
