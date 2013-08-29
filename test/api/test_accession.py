import test.api as test

import bauble
import bauble.db as db
import bauble.i18n
from bauble.model.family import Family
from bauble.model.genus import Genus
from bauble.model.taxon import Taxon
from bauble.model.accession import Accession, AccessionNote, Verification, Voucher
from bauble.model.source import Source, SourceDetail, Collection
from bauble.model.propagation import Propagation, PlantPropagation, PropSeed, PropCutting


def test_accession_json():
    family = Family(family=test.get_random_name())
    genus_name = test.get_random_name()
    genus = Genus(family=family, genus=genus_name)
    taxon = Taxon(genus=genus, sp=test.get_random_name())
    acc = Accession(taxon=taxon, code=test.get_random_name())
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
                                date="2011/1/1", level=1, taxon=taxon,
                                prev_taxon=taxon)
    voucher = Voucher(accession=acc, herbarium=test.get_random_name(),
                      code=test.get_random_name())

    note = AccessionNote(accession=acc, note="this is a test")

    session = db.connect(test.default_user, test.default_password)
    all_objs = [family, genus, taxon, note, acc, source]
    session.add_all(all_objs)
    session.commit()

    acc_json = acc.json(depth=0)
    assert 'ref' in acc_json
    assert acc_json['ref'] == '/accession/' + str(acc.id)

    acc_json = acc.json(depth=1)
    assert 'str' in acc_json
    assert acc_json['taxon'] == taxon.json(depth=0)

    acc_json = acc.json(depth=2)
    assert 'str' in acc_json
    # add all deph=2 fields

    note_json = note.json(depth=0)
    assert 'ref' in note_json

    note_json = note.json(depth=1)
    assert 'accession' in note_json
    assert note_json['accession'] == acc.json(depth=0)

    source_json = source.json(depth=0)
    assert 'ref' in source_json

    source_json = source.json(depth=1)
    source_json = source.json(depth=2)

    # now switch the source propagation to UnrootedCuttings....

    # if we don't delete explicity then delete-orphan doesn't happen
    # on the PropSeed...last tested with SA 0.8.2pp
    session.delete(source.propagation)
    source.propagation = Propagation(prop_type='UnrootedCutting')
    source.propagation.cutting = PropCutting()

    # source.plant_propagation = Propagation(prop_type='UnrootedCutting')
    # source.plant_propagation.cutting = PropCutting()

    source_json = source.json(depth=0)
    source_json = source.json(depth=1)
    source_json = source.json(depth=2)

    ver_json = verification.json(depth=0)
    ver_json = verification.json(depth=1)
    ver_json = verification.json(depth=2)

    voucher_json = voucher.json(depth=0)
    voucher_json = voucher.json(depth=1)
    voucher_json = voucher.json(depth=2)

    map(lambda o: session.delete(o), all_objs)
    session.commit()
    session.close()


def test_server():
    """
    Test the server properly handle /taxon resources
    """

    family = test.create_resource('/family', {'family': test.get_random_name()})
    genus = test.create_resource('/genus', {'genus': test.get_random_name(),
                                 'family': family})
    taxon = test.create_resource('/taxon', {'genus': genus, 'sp': test.get_random_name()})

    # source_detail = test.create_resource('/sourcedetail', {
    #     'name': test.get_random_name(),
    #     'source_type': "BG"
    # })

    # create a accession accession
    first_accession = test.create_resource('/accession', {
        'taxon': taxon,
        'code': test.get_random_name()#,

        # 'source': {
        #     'sources_id': test.get_random_name(),
        #     'source_detail': source_detail,
        #     'collection': {
        #         "locale": test.get_random_name()
        #     },
        #     'propagation': {
        #         'prop_type': 'UnrootedCutting',
        #         'details': {
        #             'media': "Fafard 3B"
        #         }
        #     }
        # },
        #'plant_propagation': {}
    })

    # create another accession and use the first as a synonym
    data = {'taxon': taxon, 'code': test.get_random_name()
            # 'notes': [{'user': 'me', 'category': 'test', 'date': '1/1/2001', 'note': 'test note'},
            #           {'user': 'me', 'category': 'test', 'date': '2/2/2001', 'note': 'test note2'}],
            # 'synonyms': [{'synonym': first_accession}]
            }

    second_accession = test.create_resource('/accession', data)
    assert 'ref' in second_accession  # created

    # update the accession
    second_accession['accession'] = test.get_random_name()
    second_ref = second_accession['ref']
    second_accession = test.update_resource(second_accession)
    assert second_accession['ref'] == second_ref  # make sure they have the same ref after the update

    # get the accession
    first_accession = test.get_resource(first_accession['ref'])

    # query for taxa
    print('second_accession', second_accession)
    response_json = test.query_resource('/accession', q=second_accession['code'])
    print(response_json)
    second_accession = response_json['results'][0]  # we're assuming there's only one
    assert second_accession['ref'] == second_ref

    # delete the created resources
    test.delete_resource(first_accession['ref'])
    test.delete_resource(second_accession['ref'])
    test.delete_resource(taxon)
    test.delete_resource(genus)
    test.delete_resource(family)
