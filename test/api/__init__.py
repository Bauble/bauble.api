import json
import os
import random

import requests
import requests.auth as auth

import bauble

# WARNING: DO NOT RUN THIS SCRIPT ON THE PRODUCTION SERVER
server = "http://localhost:9090"
api_root = server + "/api/v1"
default_user = "admin"


if "api.bauble.io" in server or os.environ.get('BAUBLE_ENV') != 'development':
    print("NOT IN PRODUCTION YOU FOOL!")


def setup_module(module):
    pass


def teardown_module(module):
    pass


def get_random_name():
    """
    Return a random string for creating resources that require unique names.
    """
    return str(random.random())


def get_headers(depth=1):
    """
    Return the standard request headers
    """
    return {'accept': 'application/json;depth=' + str(depth)}


def count_resource(resource):
    response = requests.get(api_root + resource + "/count")
    assert response.status_code == 200
    return response.text


def get_schema(resource):
    response = requests.get(api_root + resource + "/schema")
    assert response.status_code == 200
    return json.loads(response.text)


def create_resource(resource, data, user=default_user, password=None):
    """
    Create a server based resource with fields in kwargs with a POST
    """
    headers = get_headers()
    headers['content-type'] = 'application/json'

    # convert data to a json string so it won't get paramaterized
    if not isinstance(data, str):
        data = json.dumps(data)

    response = requests.post(api_root + resource, data=data, headers=headers,
                             auth=auth.HTTPBasicAuth(user, password))

    assert response.status_code == 201
    return json.loads(response.text)


def update_resource(data, user=default_user, password=None):
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
    response = requests.put(resource, data=data, headers=headers)
    assert response.status_code == 200
    return json.loads(response.text)


def get_resource(ref, depth=1, relations=[], user=default_user, password=None):
    """
    Get a server based resource with id=id
    """
    if(not ref.startswith(api_root)):
        ref = api_root + ref
    params = {}
    if relations:
        params['relations'] = relations
    response = requests.get(ref, headers=get_headers(depth=depth), params=params)
    #print('response: ', response.text)
    assert response.status_code == 200
    return json.loads(response.text)


def query_resource(resource, q, depth=1, relations=[], user=default_user, password=None):
    """
    """
    if not resource.startswith(api_root):
        resource = api_root + resource
    params = { 'q': q }
    if(relations):
        params['relations'] = str(relations)
    response = requests.get(resource, params=params, headers=get_headers(depth=depth))
    assert response.status_code == 200
    return json.loads(response.text)


def delete_resource(ref, user=default_user, password=None):
    """
    Delete a server based resource with id=id
    """
    # if not a string assume its a JSON resource object
    if not isinstance(ref, str):
        ref = ref['ref']
    if(not ref.startswith(api_root)):
        ref = api_root + ref
    print('deleting ', ref)
    response = requests.delete(ref, auth=auth.HTTPBasicAuth(user, password))
    assert response.status_code == 200
    return response
