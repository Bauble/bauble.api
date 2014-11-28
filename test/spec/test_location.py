import pytest

import bauble.db as db
from bauble.model.location import Location

import test.api as api


@pytest.fixture
def setup(organization, session):
    setup.organization = session.merge(organization)
    setup.user = setup.organization.owners[0]
    setup.session = session
    db.set_session_schema(session, setup.organization.pg_schema)
    return setup


def test_location_json(setup):

    session = setup.session

    code = api.get_random_name()[0:9]
    location = Location(code=code)

    session.add(location)
    session.commit()

    location_json = location.json()
    assert 'id' in location_json
    assert location_json['id'] == location.id
    assert 'code' in location_json
    assert 'str' in location_json

    session.delete(location)
    session.commit()
    session.close()


def test_server(setup):
    """
    Test the server properly handle /location resources
    """

    user = setup.user

    # create a location
    location = api.create_resource('/location', {'code': api.get_random_name()[0:9]}, user)

    assert 'id' in location  # created
    location_id = location['id']
    location['code'] = api.get_random_name()[0:9]
    location = api.update_resource('/location/{}'.format(location_id), location, user)
    assert location['id'] == location_id

    # get the location
    location = api.get_resource('/location/{}'.format(location['id']), user=user)

    # query for locations
    locations = api.query_resource('/location', q=location['code'], user=user)
    assert location['id'] in [location['id'] for location in locations]

    # delete the created resources
    api.delete_resource('/location/{}'.format(location['id']), user)
