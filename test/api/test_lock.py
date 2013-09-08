
import requests

import test.api as test
import bauble.db as db
from bauble.model.family import Family, FamilySynonym, FamilyNote

def test_lock():
    # create a family family
    family = test.create_resource('/family', {'family': test.get_random_name()})
    url = test.api_root + family['ref'] + "/lock"
    response = requests.post(url, auth=(test.default_user, test.default_password))
    assert response.status_code == 201

    lock = json.loads(response.text)

    # get the lock description
    response = requests.get(url, auth=(test.default_user, test.default_password))
    assert response.status_code == 200

    # don't allow other users to delete the lock
    response = requests.delete(url, auth=('test2', 'test2'))
    assert response.status_code == 200
