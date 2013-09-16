
import test.api as api
import bauble.db as db
from bauble.model.location import Location


def test_location_json():
    code = api.get_random_name()[0:9]
    location = Location(code=code)

    session = db.connect(api.default_user, api.default_password)
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


def test_server():
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
    response_json = api.query_resource('/location', q=location['code'])
    location = response_json['results'][0]  # we're assuming there's only one
    assert location['ref'] == location_ref

    # delete the created resources
    api.delete_resource(location)
