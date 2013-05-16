
import test.api as test    


def test_organization():
    
    # create a new organization
    data = {
        "name": test.get_random_name()
    }

    org = test.create_resource("/organization", data)
    assert org['name'] == data['name']

    # delete the organization
    test.delete_resource(org['ref'])
    
    
