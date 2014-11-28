import pytest

import bauble.db as db
from bauble.model.family import Family
from bauble.model.genus import Genus, GenusSynonym, GenusNote
import test.api as api

@pytest.fixture
def setup(organization, session):
    setup.organization = session.merge(organization)
    setup.user = setup.organization.owners[0]
    setup.session = session
    db.set_session_schema(session, setup.organization.pg_schema)
    return setup


def test_genus_json(setup):
    session = setup.session

    family = Family(family=api.get_random_name())
    genus_name = api.get_random_name()
    genus = Genus(family=family, genus=genus_name)
    note = GenusNote(genus=genus, note="this is a test")
    syn = GenusSynonym(genus=genus, synonym=genus)

    session.add_all([family, genus, note, syn])
    session.commit()

    genus_json = genus.json()
    assert 'id' in genus_json
    assert genus_json['id'] == genus.id
    assert 'genus' in genus_json
    assert 'str' in genus_json
    assert 'qualifier' in genus_json

    note_json = note.json()
    assert 'id' in note_json
    assert 'genus_id' in note_json
    assert note_json['genus_id'] == genus.id

    syn_json = syn.json()
    assert 'id' in syn_json
    assert syn_json['genus_id'] == genus.id
    assert syn_json['synonym_id'] == genus.id

    session.delete(genus)
    session.commit()
    session.close()


def test_server(setup):
    """
    Test the server properly handle /genus resources
    """
    user = setup.user

    family = api.create_resource('/family', {'family': api.get_random_name()}, user)

    # create a genus
    first_genus = api.create_resource('/genus', {'genus': api.get_random_name(), 'family': family},
                                      user)

    # create another genus and use the first as a synonym
    data = {'genus': api.get_random_name(),
            'family': family,
            'notes': [{'user': 'me', 'category': 'test', 'date': '2001-1-1',
                       'note': 'test note'},
                      {'user': 'me', 'category': 'test', 'date': '2002-2-2',
                       'note': 'test note2'}],
            'synonyms': [first_genus]
            #'synonyms': [{'synonym': first_genus}]
            }

    second_genus = api.create_resource('/genus', data, user)
    assert 'id' in second_genus  # created

    # update the genus
    second_genus['genus'] = api.get_random_name()
    second_id = second_genus['id']
    second_genus = api.update_resource('/genus/' + str(second_id), second_genus, user=user)
    assert second_genus['id'] == second_id  # make sure they have the same id after the update

    # get the genus
    first_genus = api.get_resource('/genus/' + str(first_genus['id']), user=user)

    # query for genera and make sure the second genus is in the results
    genera = api.query_resource('/genus', q=second_genus['genus'], user=user)
    # TODO: ** shouldn't len(genera) be 1 since the name should be unique
    #assert second_genus['ref'] in [genus['ref'] for genus in genera]
    assert second_genus['id'] in [genus['id'] for genus in genera]

    # test getting the genus relative to its family

    # ** TODO: now we just embed the relation in the /genera/:id
    # ** request....need to create a test to make sure it's happening
    # genera = api.get_resource('/family/' + str(family['id']) + "/genera", user=user)
    # assert first_genus['id'] in [genus['id'] for genus in genera]

    # test getting a family with its genera relations
    # ** TODO: now we just embed the relation in the /genera/:id
    # ** request....need to create a test to make sure it's happening
    #response_json = api.query_resource('/family', q=family['family'], relations="genera,notes", user=user)
    #families = response_json

    # TODO: *** i don't know if we still support returning relations like this...do
    # we need to
    # print(families[0]['genera'])
    # assert first_genus['ref'] in [genus['ref'] for genus in families[0]['genera']]

    # count the number of genera on a family
    # TODO: ** count is temporarily disabled
    # count = api.count_resource(family['ref'] + "/genera")
    # assert count == "2"

    # delete the created resources
    api.delete_resource('/genus/' + str(first_genus['id']), user)
    api.delete_resource('/genus/' + str(second_genus['id']), user)
    api.delete_resource('/family/' + str(family['id']), user)
