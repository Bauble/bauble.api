from datetime import datetime

import pytest

import bauble.db as db
from bauble.model.family import Family
from bauble.model.genus import Genus
from bauble.model.taxon import Taxon
from bauble.model.accession import Accession
from bauble.model.plant import Plant, PlantNote
from bauble.model.location import Location

import test.api as api


def plant_ref(id):
    return '/plant/{}'.format(id)

@pytest.fixture
def setup(organization, session):
    setup.organization = session.merge(organization)
    setup.user = setup.organization.owners[0]
    setup.session = session
    db.set_session_schema(session, setup.organization.pg_schema)
    return setup


def test_plant_json(setup):

    session = setup.session

    family = Family(family=api.get_random_name())
    genus_name = api.get_random_name()
    genus = Genus(family=family, genus=genus_name)
    taxon = Taxon(genus=genus, sp=api.get_random_name())
    acc = Accession(taxon=taxon, code=api.get_random_name())
    location = Location(code=api.get_random_name()[0:9])
    plant = Plant(accession=acc, code=api.get_random_name()[0:5],
                  quantity=1, location=location)

    note = PlantNote(plant=plant, note="this is a test")

    all_objs = [family, genus, taxon, note, acc, plant, location]
    session.add_all(all_objs)
    session.commit()

    plant_json = plant.json()
    assert 'id' in plant_json
    assert plant_json['id'] == plant.id
    assert 'str' in plant_json

    note_json = note.json()
    assert 'id' in note_json
    assert 'plant_id' in note_json
    assert note_json['plant_id'] == plant.id

    map(lambda o: session.delete(o), all_objs)
    session.commit()
    session.close()


def test_server(setup):
    """
    Test the server properly handle /taxon resources
    """

    user = setup.user

    family = api.create_resource('/family', {'family': api.get_random_name()}, user)
    genus = api.create_resource('/genus', {'genus': api.get_random_name(),
                                           'family': family}, user)
    taxon = api.create_resource('/taxon', {'genus': genus, 'sp': api.get_random_name()}, user)
    accession = api.create_resource('/accession',
                                    {'taxon': taxon, 'code': api.get_random_name()}, user)
    location = api.create_resource('/location', {'code': api.get_random_name()[0:9]}, user)
    location2 = api.create_resource('/location', {'code': api.get_random_name()[0:9]}, user)

    plant = api.create_resource('/plant', {
        'accession': accession, 'location': location,
        'code': api.get_random_name()[0:5],
        'quantity': 10}, user)


    # update the plant, add 2
    assert 'id' in plant  # created
    plant_id = plant['id']
    plant['code'] = api.get_random_name()[0:5]
    plant['quantity'] = plant['quantity'] + 2
    plant['change'] = {
        #'reason': 'No reason really.',
        'date': datetime.now().isoformat()
    }
    plant = api.update_resource(plant_ref(plant_id), plant, user)
    assert plant['id'] == plant_id
    plant = api.get_resource(plant_ref(plant['id']), user=user)
    assert isinstance(plant['changes'], list)
    assert plant['changes'][-1]['quantity'] == 2
    assert plant['changes'][-1]['from_location_id'] == location['id']
    assert plant['changes'][-1]['to_location_id'] is None

    # update the plant and remove 3
    plant['quantity'] = plant['quantity'] - 3
    plant['change'] = {
        #'reason': 'No reason really.',
        'date': datetime.now().isoformat()
    }
    plant = api.update_resource(plant_ref(plant_id), plant, user)
    assert plant['id'] == plant_id
    plant = api.get_resource(plant_ref(plant['id']), user=user)
    assert isinstance(plant['changes'], list)
    assert plant['changes'][-1]['quantity'] == -3
    assert plant['changes'][-1]['from_location_id'] == location['id']
    assert plant['changes'][-1]['to_location_id'] is None


    # move some of the plants to a new location
    change_quantity = plant['quantity'] - 4
    plant['quantity'] = change_quantity
    plant['location_id'] = location2['id']
    plant['change'] = {
        'reason': 'No reason really.',
        'date': datetime.now().isoformat()
    }
    plant = api.update_resource(plant_ref(plant_id), plant, user)
    assert plant['id'] == plant_id
    plant = api.get_resource(plant_ref(plant['id']), user=user)
    assert isinstance(plant['changes'], list)
    assert plant['changes'][-1]['quantity'] == change_quantity
    assert plant['changes'][-1]['from_location_id'] == location['id']
    assert plant['changes'][-1]['to_location_id'] == location2['id']

    # query for plants
    plants = api.query_resource('/plant', q=plant['code'], user=user)
    assert plant['id'] in [plant['id'] for plant in plants]

    # delete the created resources
    api.delete_resource('/plant/' + str(plant['id']), user)
    api.delete_resource('/location/' + str(location['id']), user)
    api.delete_resource('/location/' + str(location2['id']), user)
    api.delete_resource('/accession/' + str(accession['id']), user)
    api.delete_resource('/taxon/' + str(taxon['id']), user)
    api.delete_resource('/genus/' + str(genus['id']), user)
    api.delete_resource('/family/' + str(family['id']), user)
