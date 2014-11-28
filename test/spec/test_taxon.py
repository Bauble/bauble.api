import pytest

import bauble.db as db
from bauble.model.family import Family
from bauble.model.genus import Genus
from bauble.model import Taxon, TaxonSynonym, TaxonNote, Geography

import test.api as api


@pytest.fixture
def setup(request, organization, session):
    setup.organization = session.merge(organization)
    setup.user = setup.organization.owners[0]
    setup.session = session
    db.set_session_schema(session, setup.organization.pg_schema)

    setup.family = Family(family=api.get_random_name())
    setup.genus = Genus(family=setup.family, genus=api.get_random_name())
    setup.session.add_all([setup.family, setup.genus])
    setup.session.commit()

    def cleanup():
        setup.session.delete(setup.genus)
        setup.session.delete(setup.family)
        setup.session.commit()

    request.addfinalizer(cleanup)

    return setup


def test_json(setup):
    session = setup.session

    taxon = Taxon(genus=setup.genus, sp=api.get_random_name())

    note = TaxonNote(taxon=taxon, note="this is a test")
    syn = TaxonSynonym(taxon=taxon, synonym=taxon)

    session.add_all([taxon, note, syn])
    session.commit()

    taxon_json = taxon.json()
    assert 'id' in taxon_json
    assert 'str' in taxon_json
    assert taxon_json['genus_id'] == setup.genus.id

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

    session.delete(taxon)
    session.commit()
    session.close()


def test_route(setup):
    """
    Test the server properly handle /taxon resources
    """

    # create a taxon taxon
    first_taxon = api.create_resource('/taxon', {
        'sp': api.get_random_name(),
        'genus_id': setup.genus.id
    }, user=setup.user)

    second_taxon = api.create_resource('/taxon', {
        'sp': api.get_random_name(),
        'genus_id': setup.genus.id
    }, user=setup.user)

    assert 'id' in second_taxon  # created

    # update the taxon
    second_taxon['sp'] = api.get_random_name()
    second_id = second_taxon['id']
    second_taxon = api.update_resource('/taxon/' + str(second_id), second_taxon,
                                       user=setup.user)
    assert second_taxon['id'] == second_id  # make sure they have the same ref after the update

    # get the taxon
    first_taxon = api.get_resource('/taxon/' + str(first_taxon['id']), user=setup.user)

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
    api.delete_resource('/taxon/' + str(first_taxon['id']), user=setup.user)
    api.delete_resource('/taxon/' + str(second_taxon['id']), user=setup.user)


def test_synonyms(setup):
    pass



def test_names(setup):
    # create a taxon taxon
    taxon = Taxon(genus=setup.genus, sp=api.get_random_name())
    setup.session.add(taxon)
    setup.session.commit()

    names_route = '/taxon/{}/names'.format(taxon.id)

    # create a vernacular name using the route
    name_json = api.create_resource(names_route, {
        'name': api.get_random_name(),
        'language': api.get_random_name()
    }, user=setup.user)

    assert 'id' in name_json

    # check the name is in the list of names
    names = api.get_resource(names_route, user=setup.user)
    assert isinstance(names, list)
    assert name_json['id'] in [name['id'] for name in names]

    # delete the name via the route
    api.delete_resource(names_route + '/{}'.format(name_json['id']), user=setup.user)

    setup.session.delete(taxon)
    setup.session.commit()


def test_distribution(setup):

    # create a taxon taxon
    taxon = Taxon(genus=setup.genus, sp=api.get_random_name())
    setup.session.add(taxon)

    geography = Geography(name='Test')
    setup.session.add(geography)
    setup.session.commit()

    dist_route = '/taxon/{}/distributions'.format(taxon.id)

    # get a geogrpahy
    #geography = setup.session.query(Geography).get(1)
    #assert geography is not None

    # add the geography to the taxon
    # create a vernacular name using the route
    dist_json = api.create_resource(dist_route, geography.json(), user=setup.user)

    # check the geography is in the distribution list
    dists = api.get_resource(dist_route, user=setup.user)
    assert isinstance(dists, list)
    assert geography.id in [dist['id'] for dist in dists]

    # delete the name via the route
    api.delete_resource(dist_route + '/{}'.format(dist_json['id']), user=setup.user)

    setup.session.delete(taxon)
    setup.session.commit()
