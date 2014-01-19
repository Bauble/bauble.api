import pytest
import sys

from test.fixtures import organization, user, session
import test.api as api
import bauble.db as db
from bauble.model.family import Family, FamilySynonym, FamilyNote

# def setup_function(function):
#     pass

# def teardown_function(function):
#     pass

def test_family_json(organization, session):
    family_name = api.get_random_name()
    family = Family(family=family_name)
    note = FamilyNote(family=family, note="this is a test")
    syn = FamilySynonym(family=family, synonym=family)

    #session = organization.get_session()
    db.set_session_schema(session, session.merge(organization).pg_schema)
    session.add_all([family, note, syn])
    session.commit()

    family_json = family.json(depth=0)
    assert 'ref' in family_json
    assert family_json['ref'] == '/family/' + str(family.id)

    family_json = family.json(depth=1)
    assert 'family' in family_json
    assert 'str' in family_json
    assert 'qualifier' in family_json

    note_json = note.json(depth=0)
    assert 'ref' in note_json

    note_json = note.json(depth=1)
    assert 'family' in note_json
    assert note_json['family'] == family.json(depth=0)

    syn_json = syn.json(depth=0)
    assert 'ref' in syn_json

    syn_json = syn.json(depth=1)
    assert syn_json['family'] == family.json(depth=0)
    assert syn_json['synonym'] == family.json(depth=0)

    session.delete(family)
    session.commit()
    session.close()


def test_get_schema(organization):
    schema = api.get_resource("/family/schema")
    assert 'genera' in schema['relations']
    assert 'notes' in schema['relations']
    #assert 'synonyms' in schema['relations']

    schema = api.get_resource("/family/genera/schema")
    assert 'genus' in schema['columns']
    assert 'taxa' in schema['relations']

    schema = api.get_resource("/family/notes/schema")
    assert 'note' in schema['columns']
    #assert 'taxon' in schema['relations']

    schema = api.get_resource("/family/genera/taxa/schema")
    assert 'sp' in schema['columns']
    assert 'accessions' in schema['relations']


def test_server(organization, session):
    """
    Test the server properly /family resources
    """

    #session = organization.get_session()
    db.set_session_schema(session, session.merge(organization).pg_schema)
    families = session.query(Family)

    # create a family family
    first_family = api.create_resource('/family', {'family': api.get_random_name()})

    # create another family and use the first as a synonym
    data = {'family': api.get_random_name(),
            'notes': [{'user': 'me', 'category': 'test', 'date': '2001/1/1', 'note': 'test note'},
                      {'user': 'me', 'category': 'test', 'date': '2002/2/2', 'note': 'test note2'}],
            'synonyms': [first_family]
            }

    second_family = api.create_resource('/family', data)
    assert 'ref' in second_family  # created

    # update the family
    second_family['family'] = api.get_random_name()
    second_ref = second_family['ref']
    second_family = api.update_resource(second_family)
    assert second_family['ref'] == second_ref  # make sure they have the same ref after the update

    # get the family
    first_family = api.get_resource(first_family['ref'])

    # query for families
    response_json = api.query_resource('/family', q=second_family['family'])
    second_family = response_json[0]  # we're assuming there's only one
    assert second_family['ref'] == second_ref
    # delete the created resources
    api.delete_resource(first_family['ref'])
    api.delete_resource(second_family['ref'])
