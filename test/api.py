from datetime import datetime, date
import json
import os
import random
import string

import requests

import bauble
from bauble.model import Model
import test


server = "http://localhost:8088"
api_root = server + "/v1"


def json_encoder(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError


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


def count_resource(resource, user=None):
    auth = (user.email, user.access_token) if user else None
    response = requests.get(api_root + resource + "/count", auth=auth)
    assert response.status_code == 200
    return response.text


def get_schema(resource, user=None):
    auth = (user.email, user.access_token) if user else None
    response = requests.get(api_root + resource + "/schema", auth=auth)
    assert response.status_code == 200
    return json.loads(response.text)


def create_resource(resource, data, user=None):
    """
    Create a server based resource with fields in kwargs with a POST
    """
    # convert data to a json string so it won't get paramaterized
    if not isinstance(data, str):
        data = json.dumps(data, default=json_encoder)

    auth = (user.email, user.access_token) if user else None
    headers = {'content-type': 'application/json'}
    response = requests.post(api_root + resource, data=data, auth=auth, headers=headers)

    assert response.status_code == 201
    return json.loads(response.text)


def update_resource(resource, data, user=None):
    """
    Create or update a server based resource using a http PUT
    """
    #resource = data['ref']
    if not resource.startswith(api_root):
        resource = api_root + resource

    # convert data to a json string so it won't get paramaterized

    if isinstance(data, Model):
        data = json.dumps(data.json())
    elif not isinstance(data, str):
        data = json.dumps(data)

    auth = (user.email, user.access_token) if user else None
    headers = {'content-type': 'application/json'}
    response = requests.patch(resource, data=data, headers=headers, auth=auth)
    assert response.status_code == 200
    return json.loads(response.text)


def get_resource(resource, params=None, user=None):
    """
    Get a server based resource with id=id
    """
    if(not resource.startswith(api_root)):
        resource = api_root + resource

    auth = (user.email, user.access_token) if user else None
    response = requests.get(resource, params=params, auth=auth)
    assert response.status_code == 200
    assert "application/json" in response.headers['content-type']
    return response.json()


def query_resource(resource, q, relations=[], user=None):
    """
    """
    if not resource.startswith(api_root):
        resource = api_root + resource
    params = {'q': q}
    if(relations):
        params['relations'] = str(relations)

    auth = (user.email, user.access_token) if user else None
    response = requests.get(resource, params=params, auth=auth)
    assert response.status_code == 200
    return json.loads(response.text)


def delete_resource(ref, user=None):
    """
    Delete a server based resource with id=id
    """
    # if not a string assume its a JSON resource object
    if not isinstance(ref, str):
        ref = ref['ref']
    if(not ref.startswith(api_root)):
        ref = api_root + ref

    auth = (user.email, user.access_token) if user else None
    response = requests.delete(ref, auth=auth)
    assert response.status_code == 204
    return response
