
import test.api as test


def test_organization():

    user_data = {
        "username": test.get_random_name(),
        "fullname": test.get_random_name(),
        "title": test.get_random_name(),
        "email": test.get_random_name() + "@google.com",
        "password": test.get_random_name()
    }

    org_data = {
        "name": test.get_random_name(),
        "owners": [user_data]
    }

    # create a new organization
    org = test.create_resource("/organization", org_data)
    assert org['name'] == data['name']
    print(org)

    owner = org['owners'][0]
    user = test.get_resource(owner['ref'], user_data['username'], user_data['password'])
    assert user['ref'] == owner['ref']
    raise

    #user = test.create_resource(org['ref'] + 'user', user_data)
    #assert user['name'] == user_data['name']
    #assert user['org']['ref'] == org['ref']

    # add another user to the organization



    # delete the organization (should also delete the users)
    test.delete_resource(org['ref'])
