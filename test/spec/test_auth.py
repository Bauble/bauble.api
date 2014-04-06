
from datetime import datetime
import json

import requests

from test.fixtures import user, session
from test.api import api_root, get_random_name


def test_auth(user, session):

    # set the password explicity so we know what it is
    password = get_random_name()
    user.password = password
    session.add(user)
    session.commit()

    # test /login
    response = requests.get(api_root + "/login", auth=(user.email, password))
    assert response.status_code == 200
    assert "application/json" in response.headers['content-type']
    user_json = response.json()
    assert len(user_json['access_token']) == 32

    # test /logout
    user = session.merge(user)
    session.refresh(user)
    assert len(user.access_token) == 32
    assert isinstance(user.access_token_expiration, datetime)
    response = requests.get(api_root + "/logout", auth=(user.email, user.access_token))
    assert response.status_code == 200
    session.refresh(user)
    assert user.access_token is None
    assert user.access_token_expiration is None


def test_forgot_password(user, session):
    user = session.merge(user)

    response = requests.post(api_root + "/forgot-password?email=" + user.email)
    assert response.status_code == 200, response.text
    session.refresh(user)
    assert user.password_reset_token is not None
    assert isinstance(user.password_reset_token, str)
    assert len(user.password_reset_token) >= 32
    #assert user.reset_password_token_expiration is not None

    response = requests.post(api_root + "/reset-password",
                             headers={'content-type': 'application/json'},
                             data=json.dumps({
                                 'email': user.email,
                                 'password': 'new_password',
                                 'token': user.password_reset_token
                             }))
    assert response.status_code == 200, response.text
    session.refresh(user)
    assert user.password_reset_token is None
