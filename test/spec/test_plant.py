
import bauble.db as db
from bauble.model.family import Family
from bauble.model.genus import Genus
from bauble.model.taxon import Taxon
from bauble.model.accession import Accession
from bauble.model.plant import Plant, PlantNote
from bauble.model.location import Location

import test.api as api
from test.fixtures import organization, user


def test_plant_json(organization):
    family = Family(family=api.get_random_name())
    genus_name = api.get_random_name()
    genus = Genus(family=family, genus=genus_name)
    taxon = Taxon(genus=genus, sp=api.get_random_name())
    acc = Accession(taxon=taxon, code=api.get_random_name())
    location = Location(code=api.get_random_name()[0:9])
    plant = Plant(accession=acc, code=api.get_random_name()[0:5],
                  quantity=1, location=location)

    note = PlantNote(plant=plant, note="this is a test")

    session = organization.get_session()
    all_objs = [family, genus, taxon, note, acc, plant, location]
    session.add_all(all_objs)
    session.commit()

    plant_json = plant.json(depth=0)
    assert 'ref' in plant_json
    assert plant_json['ref'] == '/plant/' + str(plant.id)

    plant_json = plant.json(depth=1)
    assert 'str' in plant_json

    plant_json = plant.json(depth=2)

    # add all deph=2 fields

    note_json = note.json(depth=0)
    assert 'ref' in note_json

    note_json = note.json(depth=1)
    assert 'plant' in note_json
    assert note_json['plant'] == plant.json(depth=0)

    map(lambda o: session.delete(o), all_objs)
    session.commit()
    session.close()


def test_server(organization):
    """
    Test the server properly handle /taxon resources
    """

    family = api.create_resource('/family', {'family': api.get_random_name()})
    genus = api.create_resource('/genus', {'genus': api.get_random_name(),
        'family': family})
    taxon = api.create_resource('/taxon', {'genus': genus, 'sp': api.get_random_name()})
    accession = api.create_resource('/accession',
        {'taxon': taxon, 'code': api.get_random_name()})
    location = api.create_resource('/location', {'code': api.get_random_name()[0:9]})

    plant = api.create_resource('/plant',
        {'accession': accession, 'location': location,
         'code': api.get_random_name()[0:5],
         'quantity': 10})

    assert 'ref' in plant  # created
    plant_ref = plant['ref']
    plant['code'] = api.get_random_name()[0:5]
    plant = api.update_resource(plant)
    assert plant['ref'] == plant_ref

    # get the plant
    plant = api.get_resource(plant['ref'])

    # query for plants
    plants = api.query_resource('/plant', q=plant['code'])
    assert plant['ref'] in [plant['ref'] for plant in plants]

    # delete the created resources
    api.delete_resource(plant)
    api.delete_resource(location)
    api.delete_resource(accession)
    api.delete_resource(taxon)
    api.delete_resource(genus)
    api.delete_resource(family)
