import pytest

import bauble.db as db
from bauble.model.family import Family
from bauble.model.genus import Genus
from bauble.model.taxon import Taxon
from bauble.model.accession import Accession, AccessionNote, Verification, Voucher
from bauble.model.source import Source, SourceDetail, Collection
from bauble.model.propagation import Propagation, PlantPropagation, PropSeed, PropCutting

import test.api as test

@pytest.fixture
def setup(request, organization, session):
    setup.organization = session.merge(organization)
    setup.user = setup.organization.owners[0]
    setup.session = session
    db.set_session_schema(session, setup.organization.pg_schema)

    setup.family = Family(family=test.get_random_name())
    setup.genus = Genus(family=setup.family, genus=test.get_random_name())
    setup.taxon = Taxon(genus=setup.genus, sp=test.get_random_name())
    setup.session.add_all([setup.family, setup.genus, setup.taxon])
    setup.session.commit()

    def cleanup():
        setup.session.delete(setup.taxon)
        setup.session.delete(setup.genus)
        setup.session.delete(setup.family)
        setup.session.commit()

    request.addfinalizer(cleanup)

    return setup


def test_json(setup):

    session = setup.session
    acc = Accession(taxon=setup.taxon, code=test.get_random_name())
    source = Source(accession=acc, sources_code=test.get_random_name())
    source.source_detail = SourceDetail(name=test.get_random_name(), description="the description")
    source.collection = Collection(locale=test.get_random_name())
    source.propagation = Propagation(prop_type='Seed')
    source.propagation.seed = PropSeed(nseeds=100, date_sown="2011/1/1")

    # TODO: plant propagations require a plant.id
    # source.plant_propagation = PlantPropagation(plant_id=)
    # source.plant_propagation.propagation = PlantPropagation(prop_type='Seed')
    # source.plant_propagation.seed = PropSeed(nseeds=100, date_sown="1/1/11")

    verification = Verification(accession=acc, verifier=test.get_random_name(),
                                date="2011/1/1", level=1, taxon=setup.taxon,
                                prev_taxon=setup.taxon)
    voucher = Voucher(accession=acc, herbarium=test.get_random_name(),
                      code=test.get_random_name())

    note = AccessionNote(accession=acc, note="this is a test")

    all_objs = [note, acc, source]
    session.add_all(all_objs)
    session.commit()

    acc_json = acc.json()
    assert 'id' in acc_json
    assert acc_json['id'] == acc.id
    assert 'str' in acc_json
    assert acc_json['taxon_id'] == setup.taxon.id

    note_json = note.json()
    assert 'id' in note_json
    assert 'accession_id' in note_json
    assert note_json['accession_id'] == acc.id

    source_json = source.json()
    assert 'id' in source_json

    # now switch the source propagation to UnrootedCuttings....

    # if we don't delete explicity then delete-orphan doesn't happen
    # on the PropSeed...last tested with SA 0.8.2pp
    session.delete(source.propagation)
    source.propagation = Propagation(prop_type='UnrootedCutting')
    source.propagation.cutting = PropCutting()

    # source.plant_propagation = Propagation(prop_type='UnrootedCutting')
    # source.plant_propagation.cutting = PropCutting()

    source_json = source.json()


    ver_json = verification.json()


    voucher_json = voucher.json()

    for obj in all_objs:
        session.delete(obj)
    session.commit()
    session.close()


def test_route(setup):
    """
    Test the server properly handle /taxon resources
    """

    user = setup.user
    source_detail = SourceDetail(name=test.get_random_name(), description="the description")
    setup.session.add(source_detail)
    setup.session.commit()

    # TODO: test that POST with taxon and taxon_id both work, same with source_detail

    # create an accession
    first_accession = test.create_resource('/accession', {
        'taxon_id': setup.taxon.id,
        'code': test.get_random_name(),
        'source': {
            'id': source_detail.id,
            'sources_code': test.get_random_name(),
            'collection': {
                "locale": test.get_random_name()
            },
            'propagation': {
                'prop_type': 'UnrootedCutting',
                'media': "Fafard 3B"
            }
        },
        # TODO: setting the plant propagation id would require us to create a second
        # accession, plant and plant propagation record and set that record
        # here
        'plant_propagation': {}
    }, user)

    # create another accession and use the first as a synonym
    data = {'taxon_id': setup.taxon.id, 'code': test.get_random_name()}

    notes = [{'user': 'me', 'category': 'test', 'date': '1/1/2001', 'note': 'test note'},
             {'user': 'me', 'category': 'test', 'date': '2/2/2001', 'note': 'test note2'}],
    synonyms = [{'synonym': first_accession}]

    second_accession = test.create_resource('/accession', data, user)
    assert 'id' in second_accession  # created

    # update the accession
    second_accession['accession'] = test.get_random_name()
    second_accession['source'] = first_accession['source']
    second_id = second_accession['id']
    second_accession = test.update_resource('/accession/' + str(second_id), second_accession, user)
    assert second_accession['id'] == second_id  # make sure they have the same ref after the update

    # get the accession
    first_accession = test.get_resource('/accession/' + str(first_accession['id']), user=user)

    # query for taxa
    accessions = test.query_resource('/accession', q=second_accession['code'], user=user)
    assert second_accession['id'] in [accession['id'] for accession in accessions]

    # delete the created resources
    test.delete_resource('/accession/' + str(first_accession['id']), user)
    test.delete_resource('/accession/' + str(second_accession['id']), user)
