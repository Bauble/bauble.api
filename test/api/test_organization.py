
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
    assert org['name'] == org_data['name']
    print(org)

    # get the org with depth=2 so we can get its relations
    org = test.get_resource(org['ref'], depth=2)
    print(org)
    owner = org['owners'][0]
    user = test.get_resource(owner['ref'])
    assert user['ref'] == owner['ref']

    #user = test.create_resource(org['ref'] + 'user', user_data)
    #assert user['name'] == user_data['name']
    #assert user['org']['ref'] == org['ref']

    # add another user to the organization
    user2_data = user_data.copy()
    user2_data['username'] = test.get_random_name()
    user2_data['organization'] = org
    user2 = test.create_resource("/user", user2_data)

    # delete the organization (should also delete the users)
    test.delete_resource(org['ref'])
