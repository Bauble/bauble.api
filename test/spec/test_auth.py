
from datetime import datetime

import requests
import requests.auth as auth

import bauble.db as db
from bauble.model.user import User
from test.fixtures import user, session
from test.api import api_root, get_random_name
import test


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
