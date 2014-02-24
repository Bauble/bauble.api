import json

import pytest
import requests

import bauble.db as db
from bauble.model.family import Family, FamilySynonym, FamilyNote
from test.fixtures import organization, user, session
import test.api as api

@pytest.fixture
def setup(organization, session):
    setup.organization = session.merge(organization)
    setup.user = setup.organization.owners[0]
    setup.session = session
    db.set_session_schema(session, setup.organization.pg_schema)
    return setup


def test_synonyms(setup):
    session = setup.session
    family = Family(family=api.get_random_name())
    family2 = Family(family=api.get_random_name())
    session.add_all([family, family2])
    session.commit()

    family.synonyms.append(family2)
    session.commit()
    assert family2 in family.synonyms

    # make sure the FamilySynonym was created
    count = session.query(FamilySynonym).filter_by(family_id=family.id,
                                                   synonym_id=family2.id).count()
    assert count == 1

    family.synonyms.remove(family2)
    session.commit()
    assert family2 not in family.synonyms

    # make sure the FamilySynonym was removed
    count = session.query(FamilySynonym).filter_by(family_id=family.id,
                                                   synonym_id=family2.id).count()
    assert count == 0

    # make sure that if a family is deleted all its synonyms get deleted
    family.synonyms.append(family2)
    session.commit()
    count = session.query(FamilySynonym).filter_by(family_id=family.id,
                                                   synonym_id=family2.id).count()
    assert count == 1
    session.delete(family)
    session.commit()
    count = session.query(FamilySynonym).filter_by(family_id=family.id,
                                                   synonym_id=family2.id).count()
    assert count == 0



def test_family_json(setup):
    session = setup.session

    family_name = api.get_random_name()
    family = Family(family=family_name)
    note = FamilyNote(family=family, note="this is a test")
    syn = FamilySynonym(family=family, synonym=family)

    #session = organization.get_session()
    #db.set_session_schema(session, session.merge(organization).pg_schema)
    session.add_all([family, note, syn])
    session.commit()

    family_json = family.json()
    assert 'id' in family_json
    assert family_json['id'] == family.id

    family_json = family.json()
    assert 'family' in family_json
    assert 'str' in family_json
    assert 'qualifier' in family_json

    note_json = note.json()
    assert 'id' in note_json
    assert note_json['note'] == note.note
    assert 'family_id' in note_json
    assert note_json['family_id'] == family.id

    syn_json = syn.json()
    assert syn_json['family_id'] == family.id
    assert syn_json['synonym_id'] == family.id

    session.delete(family)
    session.commit()
    session.close()


def test_get_schema(setup):

    organization = setup.organization
    session = setup.session
    user = setup.user

    schema = api.get_resource("/family/schema", user=user)
    assert 'genera' in schema['relations']
    assert 'notes' in schema['relations']
    #assert 'synonyms' in schema['relations']

    schema = api.get_resource("/family/genera/schema", user=user)
    assert 'genus' in schema['columns']
    assert 'taxa' in schema['relations']

    schema = api.get_resource("/family/notes/schema", user=user)
    assert 'note' in schema['columns']
    #assert 'taxon' in schema['relations']

    schema = api.get_resource("/family/genera/taxa/schema", user=user)
    assert 'sp' in schema['columns']
    assert 'accessions' in schema['relations']


def test_index(setup):
    session = setup.session
    user = setup.user

    families = []
    for num in range(0, 5):
        families.append(Family(family=api.get_random_name()))
    session.add_all(families)
    session.commit()

    # a list request should work
    response = api.get_resource('/family', user=user)
    assert isinstance(response, list)

    # a list request with a filter should work
    filter = json.dumps({'family': families[0].family[0:4] + "%"})
    response = api.get_resource('/family?filter={}'.format(filter), user=user)
    assert isinstance(response, list)
    assert response[0]['family'] == families[0].family

    for family in families:
        session.delete(family)
    session.commit()


def test_patch(setup):
    session = setup.session
    user = setup.user

    family = Family(family=api.get_random_name())
    session.add(family)
    session.commit()

    family.family = family.family + "_patched"

    # should fail with a 400 response if there is no request body
    response = requests.request('PATCH', '{}/family/{}'.format(api.api_root, family.id),
                                auth=(user.email, user.access_token),
                                headers = {'content-type': 'application/json'})
    assert response.status_code == 400, response.body

    data = json.dumps(family.json())
    api.update_resource('/family/{}'.format(family.id), data, user)
    session.delete(family)
    session.commit()




def test_route(setup):
    """
    Test the /family resource.
    """

    #session = organization.get_session()
    #db.set_session_schema(session, session.merge(organization).pg_schema)
    session = setup.session
    user = setup.user

    # create a family family
    first_family = api.create_resource('/family', {'family': api.get_random_name()}, user)

    # create another family and use the first as a synonym
    data = {'family': api.get_random_name(),
            'notes': [{'user': 'me', 'category': 'test', 'date': '2001/1/1', 'note': 'test note'},
                      {'user': 'me', 'category': 'test', 'date': '2002/2/2', 'note': 'test note2'}],
            'synonyms': [first_family]
            }

    second_family = api.create_resource('/family', data, user)
    assert 'id' in second_family  # created

    # update the family
    second_family['family'] = api.get_random_name()
    second_id = second_family['id']
    second_family = api.update_resource('/family/{}'.format(second_id), second_family, user)
    assert second_family['id'] == second_id  # make sure they have the same ref after the update

    # get the family
    first_family = api.get_resource('/family/{}'.format(first_family['id']), user=user)

    # query for families
    #response_json = api.query_resource('/family', q=second_family['family'], user=user)
    filter_by = json.dumps({'family': second_family['family'][0:4] + '%'})
    response_json = api.get_resource('/family', {'filter': filter_by}, user=user)
    assert len(response_json) == 1
    second_family = response_json[0]  # we're assuming there's only one
    assert second_family['id'] == second_id

    # make sure filtering against properties that aren't columns doesn't work
    filter_by = json.dumps({'something': 'test'})
    response_json = api.get_resource('/family', {'filter': filter_by}, user=user)
    assert len(response_json) > 1

    # delete the created resources
    api.delete_resource('/family/{}'.format(first_family['id']), user)
    api.delete_resource('/family/{}'.format(second_family['id']), user)


def test_embed(setup):
    session = setup.session
    user = setup.user

    family = Family(family=api.get_random_name())
    family2 = Family(family=api.get_random_name())
    family.synonyms.append(family2)
    session.add_all([family, family2])
    session.commit()

    response = requests.get('{}/family/{}?embed=synonyms&embed=notes'.format(api.api_root, family.id), auth=(user.email, user.access_token))
    # response_json = api.get_resource('/family/{}'.format(family.id),
    #                                  {'embed': ['synonyms', 'notes']}, user=user)
    print('response: ', response)
    assert response.status_code == 200
    response_json = response.json()
    print('response_json: ', response_json)
