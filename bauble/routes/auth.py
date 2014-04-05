
import email
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import os
import random
import smtplib
import string

import bottle
from bottle import request
import sqlalchemy as sa

import bauble
import bauble.db as db
from bauble import app, API_ROOT
from bauble.middleware import basic_auth
from bauble.model import User


def create_unique_token(size=32):
    rand = random.SystemRandom()
    token = ''.join([rand.choice(string.ascii_letters + string.digits)
                     for i in range(size)])
    return token

def create_access_token():
    return create_unique_token(), datetime.now() + timedelta(weeks=2)


def create_password_reset_token():
    return create_unique_token(), datetime.now() + timedelta(weeks=2)


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


@app.post(API_ROOT + "/forgot-password")
def forgot_password():

    user_email = request.params.get('email', None)
    if not user_email and not user_email.contains('@'):
        bottle.abort("Valid email address required")

    session = None
    try:
        session = db.Session()
        user = session.query(User).filter_by(email=user_email).one()
        token, expiration = create_password_reset_token()
        # TODO: need to set the expiration
        user.password_reset_token = token
        session.commit()
    except Exception as exc:
        print(exc)
        bottle.abort(400, "Could not get a user with the requested email address")
    finally:
        if session:
            session.close()

    # send the reset password email
    use_ssl = os.environ.get("BAUBLE_SMTP_USE_SSL", "false")
    host = os.environ.get("BAUBLE_SMTP_HOST", "")
    port = os.environ.get("BAUBLE_SMTP_PORT", 0)
    user = os.environ.get("BAUBLE_SMTP_USERNAME", None)
    password = os.environ.get("BAUBLE_SMTP_PASSWORD", None)
    app_url = os.environ.get("BAUBLE_APP_URL", 'http://app.bauble.io')
    support_email = os.environ.get("BAUBLE_SUPPORT_EMAIL", "support@bauble.io")

    mappings = {'token': token, 'email': user_email, 'app_url': app_url}
    template_file = os.path.join(bauble.__path__[0], 'templates', 'reset_password.txt')
    content = open(template_file).read().format_map(mappings)

    timeout = 10  # 10 second timeout for smtp connection
    SMTP = smtplib.SMTP_SSL if use_ssl or use_ssl.lower() == "true" else smtplib.SMTP

    # **************************************************
    # don't send the email if we're running the tests
    # **************************************************
    if os.environ.get("BAUBLE_TEST", "false") == "true":
        return

    try:
        message = MIMEText(content, 'plain')
        message['subject'] = "Bauble Password Reset"
        message['reply-to'] = "support@bauble.io"
        with SMTP(host, port, timeout=timeout) as smtp:
            smtp.login(user, password)
            smtp.send_message(message, support_email, user_email)
    except smtplib.SMTPException as exc:
        # TODO: we should use logging instead of print()ing this to
        # stdout
        print(exc)
        bottle.abort(500, 'Could not send reset password email.')



@app.post(API_ROOT + "/reset-password")
def reset_password():
    session = None

    try:
        session = db.Session()
        user = session.query(User).filter_by(email=request.json['email']).first()
        if not user:
            # TODO: is this the correct status code?
            bottle.abort(422, 'A user could be be found with the provided email')

        if request.json['token'] != user.password_reset_token:
            # TODO: is this the correct status code?
            bottle.abort(422, 'Invalid password reset token')

        # TODO: need to set the expiration
        user.password_reset_token = None
        #user.password_reset_token_expiration = None
        user.password = request.json['password']
        user.access_token, user.access_token_expiration = create_access_token()
        user.last_accesseed = datetime.now()
        session.commit()
        user_json = user.json()

    except Exception as exc:
        print(exc)
        bottle.abort(400, "Could not get a user with the requested email address")
    finally:
        if session:
            session.close()

    return user_json
