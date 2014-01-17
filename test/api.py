import json
import os
import random
import string

import requests
import requests.auth as auth

import bauble
import test

# WARNING: DO NOT RUN THIS SCRIPT ON THE PRODUCTION SERVER
server = "http://localhost:9099"
api_root = server + "/api/v1"
default_user = test.default_user
default_password = test.default_password


if "api.bauble.io" in server or os.environ.get('BAUBLE_ENV') != 'development':
    print("NOT IN PRODUCTION YOU FOOL!")


def setup_module(module):
    pass


def teardown_module(module):
    pass


def get_random_name(nchars=12):
    """
    Return a random string for creating resources that require unique names.
    """
    #return str(random.random())

    # TODO: change everything to user test.utils.random_str
    return ''.join(random.choice(string.ascii_lowercase) for x in range(nchars))


def get_headers(depth=1):
    """
    Return the standard request headers
    """
    return {'accept': 'application/json;depth=' + str(depth)}


def count_resource(resource, user=default_user, password=default_password):
    response = requests.get(api_root + resource + "/count", auth=(user, password))
    assert response.status_code == 200
    return response.text


def get_schema(resource, user=default_user, password=default_password):
    response = requests.get(api_root + resource + "/schema", auth=(user, password))
    assert response.status_code == 200
    return json.loads(response.text)


def create_resource(resource, data, user=default_user, password=default_password):
    """
    Create a server based resource with fields in kwargs with a POST
    """
    headers = get_headers()
    headers['content-type'] = 'application/json'

    # convert data to a json string so it won't get paramaterized
    if not isinstance(data, str):
        data = json.dumps(data)

    response = requests.post(api_root + resource, data=data, headers=headers,
                             auth=(user, password))

    assert response.status_code == 201
    return json.loads(response.text)


def update_resource(data, user=default_user, password=default_password):
    """
    Create or update a server based resource using a http PUT
    """
    headers = get_headers()
    headers['content-type'] = 'application/json'
    resource = data['ref']
    if not resource.startswith(api_root):
        resource = api_root + resource

    # convert data to a json string so it won't get paramaterized
    if not isinstance(data, str):
        data = json.dumps(data)
    response = requests.patch(resource, data=data, headers=headers,
                            auth=(user,password))
    assert response.status_code == 200
    return json.loads(response.text)


def get_resource(ref, depth=1, relations=[], user=default_user,
                 password=default_password):
    """
    Get a server based resource with id=id
    """
    if(not ref.startswith(api_root)):
        ref = api_root + ref
    params = {}
    if relations:
        params['relations'] = relations
    response = requests.get(ref, headers=get_headers(depth=depth), params=params,
                            auth=(user,password))
    #print('response: ', response.text)
    assert response.status_code == 200
    return json.loads(response.text)


def query_resource(resource, q, depth=1, relations=[], user=default_user,
                   password=default_password):
    """
    """
    if not resource.startswith(api_root):
        resource = api_root + resource
    params = { 'q': q }
    if(relations):
        params['relations'] = str(relations)
    response = requests.get(resource, params=params, headers=get_headers(depth=depth),
                            auth=(user,password))
    assert response.status_code == 200
    return json.loads(response.text)


def delete_resource(ref, user=default_user, password=default_password):
    """
    Delete a server based resource with id=id
    """
    # if not a string assume its a JSON resource object
    if not isinstance(ref, str):
        ref = ref['ref']
    if(not ref.startswith(api_root)):
        ref = api_root + ref
    response = requests.delete(ref, auth=(user,password))
    assert response.status_code == 200
    return response
