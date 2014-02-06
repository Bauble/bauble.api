#import pytest
#import sys

from test.fixtures import organization, user, session
#import test.api as api
#import bauble.db as db
from bauble.model.user import User


def xtest_user_json(session):

    username = 'test_user_json'
    password = username

    users = session.query(User).filter_by(username=username)
    for user in users:
        session.delete(user)
    session.commit()

    user = User(username=username, password=password)
    session.add(user)
    session.commit()


def xtest_get_schema():
    schema = api.get_resource("/user/schema")


def xtest_resource(session):
    """
    Test the server properly /family resources
    """

    return
    #session = organization.get_session()
    db.set_session_schema(session, session.merge(organization).pg_schema)
    families = session.query(Family)

    # create a family family
    first_family = api.create_resource('/family', {'family': api.get_random_name()})

    # get the family
    first_family = api.get_resource(first_family['ref'])

    # query for families
    response_json = api.query_resource('/family', q=second_family['family'])
    second_family = response_json[0]  # we're assuming there's only one
    assert second_family['ref'] == second_ref
    # delete the created resources
    api.delete_resource(first_family['ref'])
    api.delete_resource(second_family['ref'])


def test_password(session):
    username = 'test_set_password'
    password = username

    print('query user')
    users = session.query(User).filter_by(username=username)
    for user in users:
        session.delete(user)
    session.commit()

    print('create user')
    user = User(username=username, password=password)
    session.add(user)
    session.commit()

    print('user.password: ', user._password)

    # test the password isn't stored in plain text
    assert user._password != password

    # test that we can compare the password against a plain test password
    assert user.password == password

    session.delete(user)
    session.commit()
    session.close()
