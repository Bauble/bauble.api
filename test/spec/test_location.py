
from bauble.model.location import Location

import test.api as api
from test.fixtures import organization, user


def test_location_json(organization):
    code = api.get_random_name()[0:9]
    location = Location(code=code)

    session = organization.get_session()
    session.add(location)
    session.commit()

    location_json = location.json(depth=0)
    assert 'ref' in location_json
    assert location_json['ref'] == '/location/' + str(location.id)

    location_json = location.json(depth=1)
    assert 'code' in location_json
    assert 'str' in location_json

    session.delete(location)
    session.commit()
    session.close()


def test_server(organization):
    """
    Test the server properly handle /location resources
    """
    # create a location
    location = api.create_resource('/location', {'code': api.get_random_name()[0:9]})

    assert 'ref' in location  # created
    location_ref = location['ref']
    location['code'] = api.get_random_name()[0:9]
    location = api.update_resource(location)
    assert location['ref'] == location_ref

    # get the location
    location = api.get_resource(location['ref'])

    # query for locations
    locations = api.query_resource('/location', q=location['code'])
    assert location['ref'] in [location['ref'] for location in locations]

    # delete the created resources
    api.delete_resource(location)
