import pytest

import bauble.db as db
from bauble.model.family import Family
from bauble.model.genus import Genus
from bauble.model.taxon import Taxon, TaxonSynonym, TaxonNote

import test.api as api
from test.fixtures import organization, user, session


@pytest.fixture
def setup(organization, session):
    setup.organization = session.merge(organization)
    setup.user = setup.organization.owners[0]
    setup.session = session
    db.set_session_schema(session, setup.organization.pg_schema)
    return setup


def test_taxon_json(setup):
    session = setup.session

    family = Family(family=api.get_random_name())
    genus_name = api.get_random_name()
    genus = Genus(family=family, genus=genus_name)
    taxon = Taxon(genus=genus, sp=api.get_random_name())

    note = TaxonNote(taxon=taxon, note="this is a test")
    syn = TaxonSynonym(taxon=taxon, synonym=taxon)

    session.add_all([family, genus, taxon, note, syn])
    session.commit()

    taxon_json = taxon.json()
    assert 'id' in taxon_json
    assert 'str' in taxon_json
    assert taxon_json['genus_id'] == genus.id

    taxon_json = taxon.json()
    assert 'str' in taxon_json
    # add all deph=2 fields

    note_json = note.json()
    assert 'id' in note_json
    assert 'taxon_id' in note_json
    assert note_json['taxon_id'] == taxon.id

    syn_json = syn.json()
    assert 'id' in syn_json
    assert syn_json['taxon_id'] == taxon.id
    assert syn_json['synonym_id'] == taxon.id

    map(lambda o: session.delete(o), [family, genus, taxon])
    session.commit()
    session.close()


def test_server(setup):
    """
    Test the server properly handle /taxon resources
    """

    user = setup.user

    family = api.create_resource('/family', {'family': api.get_random_name()}, user=user)
    genus = api.create_resource('/genus', {'genus': api.get_random_name(),
                                           'family': family}, user=user)

    # create a taxon taxon
    first_taxon = api.create_resource('/taxon', {'sp': api.get_random_name(), 'genus': genus},
                                      user=user)

    # create another taxon and use the first as a synonym
    data = {'sp': api.get_random_name(), 'genus': genus,
            # 'notes': [{'user': 'me', 'category': 'test', 'date': '1/1/2001', 'note': 'test note'},
            #           {'user': 'me', 'category': 'test', 'date': '2/2/2001', 'note': 'test note2'}],
            #'synonyms': [first_taxon]
            }

    second_taxon = api.create_resource('/taxon', data, user=user)
    assert 'id' in second_taxon  # created

    # update the taxon
    second_taxon['sp'] = api.get_random_name()
    second_id = second_taxon['id']
    second_taxon = api.update_resource('/taxon/' + str(second_id), second_taxon, user=user)
    assert second_taxon['id'] == second_id  # make sure they have the same ref after the update

    # get the taxon
    first_taxon = api.get_resource('/taxon/' + str(first_taxon['id']), user=user)

    # query for taxa
    # print('data[sp]: ' + str(data['sp']))
    # print('second_taxon', second_taxon)
    # response_json = api.query_resource('/taxon', q=data['sp'])
    # print(response_json)
    # second_taxon = response_json['results'][0]  # we're assuming there's only one
    # assert second_taxon['ref'] == second_ref

    # test getting the taxon relative to its family
    # ** TODO: now we just embed the relation in the /taxon/:id
    # ** request....need to create a test to make sure it's happening
    # taxa = api.get_resource('/family/{}/genera/taxa'.format(family['id']), user=user)
    # assert first_taxon['id'] in [taxon['id'] for taxon in taxa]

    # delete the created resources
    api.delete_resource('/taxon/' + str(first_taxon['id']), user=user)
    api.delete_resource('/taxon/' + str(second_taxon['id']), user=user)
    api.delete_resource('/genus/' + str(genus['id']), user=user)
    api.delete_resource('/family/' + str(family['id']), user=user)
