import test.api as api
import bauble.db as db
from bauble.model.family import Family
from bauble.model.genus import Genus, GenusSynonym, GenusNote


def test_genus_json():
    family = Family(family=api.get_random_name())
    genus_name = api.get_random_name()
    genus = Genus(family=family, genus=genus_name)
    note = GenusNote(genus=genus, note="this is a test")
    syn = GenusSynonym(genus=genus, synonym=genus)

    session = db.connect(api.default_user, api.default_password)
    session.add_all([family, genus, note, syn])
    session.commit()

    genus_json = genus.json(depth=0)
    assert 'ref' in genus_json
    assert genus_json['ref'] == '/genus/' + str(genus.id)

    genus_json = genus.json(depth=1)
    assert 'genus' in genus_json
    assert 'str' in genus_json
    assert 'qualifier' in genus_json

    note_json = note.json(depth=0)
    assert 'ref' in note_json

    note_json = note.json(depth=1)
    assert 'genus' in note_json
    assert note_json['genus'] == genus.json(depth=0)

    syn_json = syn.json(depth=0)
    assert 'ref' in syn_json

    syn_json = syn.json(depth=1)
    assert syn_json['genus'] == genus.json(depth=0)
    assert syn_json['synonym'] == genus.json(depth=0)

    session.delete(genus)
    session.commit()
    session.close()


def test_server():
    """
    Test the server properly handle /genus resources
    """

    family = api.create_resource('/family', {'family': api.get_random_name()})

    # create a genus
    first_genus = api.create_resource('/genus',
        {'genus': api.get_random_name(), 'family': family})

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

    second_genus = api.create_resource('/genus', data)
    assert 'ref' in second_genus  # created

    # update the genus
    second_genus['genus'] = api.get_random_name()
    second_ref = second_genus['ref']
    second_genus = api.update_resource(second_genus)
    assert second_genus['ref'] == second_ref  # make sure they have the same ref after the update

    # get the genus
    first_genus = api.get_resource(first_genus['ref'])

    # query for genera
    response_json = api.query_resource('/genus', q=second_genus['genus'])
    second_genus = response_json['results'][0]  # we're assuming there's only one
    assert second_genus['ref'] == second_ref

    # test getting the genus relative to its family
    response_json = api.get_resource(family['ref'] + "/genera")
    genera = response_json['results']
    assert first_genus['ref'] in [genus['ref'] for genus in genera]

    # test getting a family with its genera relations
    response_json = api.query_resource('/family', q=family['family'], depth=2,
        relations="genera,notes")
    families = response_json['results']
    print(families[0])
    print(families[0]['genera'])
    assert first_genus['ref'] in [genus['ref'] for genus in families[0]['genera']]

    # count the number of genera on a family
    count = api.count_resource(family['ref'] + "/genera")
    assert count == "2"

    # delete the created resources
    api.delete_resource(first_genus['ref'])
    api.delete_resource(second_genus['ref'])
    api.delete_resource(family)
