#
# plant.py
#
"""
Defines the plant table and handled editing plants
"""

from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.orm.session import object_session
from sqlalchemy.exc import DBAPIError

import bauble.db as db
#from bauble.error import check, CheckConditionError

from bauble.model import Model
from bauble.model.location import Location
from bauble.model.propagation import PlantPropagation
import bauble.types as types
import bauble.utils as utils
import bauble.search as search


# TODO: do a magic attribute on plant_id that checks if a plant id
# already exists with the accession number, this probably won't work
# though sense the acc_id may not be set when setting the plant_id

# TODO: might be worthwhile to have a label or textview next to the
# location combo that shows the description of the currently selected
# location

plant_delimiter_key = 'plant_delimiter'
default_plant_delimiter = '.'


def plant_markup_func(plant):
    '''
    '''
    sp_str = plant.accession.taxon_str(markup=True)
    #dead_color = "#777"
    dead_color = "#9900ff"
    if plant.quantity <= 0:
        dead_markup = '<span foreground="%s">%s</span>' % \
            (dead_color, utils.xml_safe_utf8(plant))
        return dead_markup, sp_str
    else:
        return utils.xml_safe_utf8(plant), sp_str


def get_next_code(acc):
    """
    Return the next available plant code for an accession.

    This function should be specific to the institution.

    If there is an error getting the next code the None is returned.
    """
    # auto generate/increment the accession code
    session = db.Session()
    codes = session.query(Plant.code).join(Accession).\
        filter(Accession.id == acc.id).all()
    next = 1
    if codes:
        try:
            next = max([int(code[0]) for code in codes]) + 1
        except Exception as e:
            return None
    return utils.utf8(next)


def is_code_unique(plant, code):
    """
    Return True/False if the code is a unique Plant code for accession.

    This method will also take range values for code that can be passed
    to utils.range_builder()
    """
    # if the range builder only creates one number then we assume the
    # code is not a range and so we test against the string version of
    # code
    codes = map(utils.utf8, utils.range_builder(code))  # test if a range
    if len(codes) == 1:
        codes = [utils.utf8(code)]

    # reference accesssion.id instead of accession_id since
    # setting the accession on the model doesn't set the
    # accession_id until the session is flushed
    session = db.Session()
    count = session.query(Plant).join('accession').\
        filter(and_(Accession.id == plant.accession.id,
                    Plant.code.in_(codes))).count()
    session.close()
    return count == 0


# TODO: what would happend if the PlantRemove.plant_id and
# PlantNote.plant_id were out of sink....how could we avoid these sort
# of cycles
class PlantNote(Model):
    __tablename__ = 'plant_note'
    __mapper_args__ = {'order_by': 'plant_note.date'}

    date = Column(types.Date, default=func.now())
    user = Column(Unicode(64))
    category = Column(Unicode(32))
    note = Column(UnicodeText, nullable=False)
    plant_id = Column(Integer, ForeignKey('plant.id'), nullable=False)
    plant = relation('Plant', uselist=False,
                     backref=backref('notes', cascade='all, delete-orphan'))



# TODO: some of these reasons are specific to UBC and could probably be culled.
change_reasons = {
    'DEAD': _('Dead'),
    'DISC': _('Discarded'),
    'DISW': _('Discarded, weedy'),
    'LOST': _('Lost, whereabouts unknown'),
    'STOL': _('Stolen'),
    'WINK': _('Winter kill'),
    'ERRO': _('Error correction'),
    'DIST': _('Distributed elsewhere'),
    'DELE': _('Deleted, yr. dead. unknown'),
    'ASS#': _('Transferred to another acc.no.'),
    'FOGS': _('Given to FOGs to sell'),
    'PLOP': _('Area transf. to Plant Ops.'),
    'BA40': _('Given to Back 40 (FOGs)'),
    'TOTM': _('Transfered to Totem Field'),
    'SUMK': _('Summer Kill'),
    'DNGM': _('Did not germinate'),
    'DISN': _('Discarded seedling in nursery'),
    'GIVE': _('Given away (specify person)'),
    'OTHR': _('Other'),
    None: ''
}


class PlantChange(Model):
    """
    """
    __tablename__ = 'plant_change'
    __mapper_args__ = {'order_by': 'plant_change.date'}

    plant_id = Column(Integer, ForeignKey('plant.id'), nullable=False)
    parent_plant_id = Column(Integer, ForeignKey('plant.id'))

    # - if to_location_id is None change is a removal
    # - if from_location_id is None then this change is a creation
    # - if to_location_id != from_location_id change is a transfer
    from_location_id = Column(Integer, ForeignKey('location.id'))
    to_location_id = Column(Integer, ForeignKey('location.id'))

    # the name of the person who made the change
    person = Column(Unicode(64))
    """The name of the person who made the change"""
    quantity = Column(Integer, autoincrement=False, nullable=False)
    note_id = Column(Integer, ForeignKey('plant_note.id'))

    reason = Column(types.Enum(values=change_reasons.keys(),
                               translations=change_reasons))

    # date of change
    date = Column(types.DateTime, default=func.now())

    # relations
    plant = relation('Plant', uselist=False,
                     primaryjoin='PlantChange.plant_id == Plant.id',
                     backref=backref('changes', cascade='all, delete-orphan'))
    parent_plant = relation('Plant', uselist=False,
                            primaryjoin='PlantChange.parent_plant_id == Plant.id',
                            backref=backref('branches', cascade='all, delete-orphan'))

    from_location = relation('Location',
                             primaryjoin='PlantChange.from_location_id == Location.id')
    to_location = relation('Location',
                           primaryjoin='PlantChange.to_location_id == Location.id')




condition_values = {
    'Excellent': _('Excellent'),
    'Good': _('Good'),
    'Fair': _('Fair'),
    'Poor': _('Poor'),
    'Questionable': _('Questionable'),
    'Indistinguishable': _('Indistinguishable Mass'),
    'UnableToLocate': _('Unable to Locate'),
    'Dead': _('Dead'),
    None: ''}

flowering_values = {
    'Immature': _('Immature'),
    'Flowering': _('Flowering'),
    'Old': _('Old Flowers'),
    None: ''}

fruiting_values = {
    'Unripe': _('Unripe'),
    'Ripe': _('Ripe'),
    None: '',
}

# TODO: should sex be recorded at the taxon, accession or plant
# level or just as part of a check since sex can change in some taxon
sex_values = {
    'Female': _('Female'),
    'Male': _('Male'),
    'Both': ''}

# class Container(Model):
#     __tablename__ = 'container'
#     __mapper_args__ = {'order_by': 'name'}
#     code = Column(Unicode)
#     name = Column(Unicode)

#
# TODO: PlantStatus was never used integrated into Bauble 1.x....???
#

class PlantStatus(Model):
    """
    date: date checked
    status: status of plant
    comment: comments on check up
    checked_by: person who did the check
    """
    __tablename__ = 'plant_status'
    date = Column(types.Date, default=func.now())
    condition = Column(types.Enum(values=condition_values.keys(),
                                  translations=condition_values))
    comment = Column(UnicodeText)
    checked_by = Column(Unicode(64))

    flowering_status = Column(types.Enum(values=flowering_values.keys(),
                                         translations=flowering_values))
    fruiting_status = Column(types.Enum(values=fruiting_values.keys(),
                                        translations=fruiting_values))

    autumn_color_pct = Column(Integer, autoincrement=False)
    leaf_drop_pct = Column(Integer, autoincrement=False)
    leaf_emergence_pct = Column(Integer, autoincrement=False)

    sex = Column(types.Enum(values=sex_values.keys(),
                            translations=sex_values))

    plant_id = Column(Integer, ForeignKey('plant.id'), nullable=False)

    # TODO: needs container table
    #container_id = Column(Integer)



acc_type_values = {'Plant': _('Plant'),
                   'Seed': _('Seed/Spore'),
                   'Vegetative': _('Vegetative Part'),
                   'Tissue': _('Tissue Culture'),
                   'Other': _('Other'),
                   None: ''}


class Plant(Model):
    """
    :Table name: plant

    :Columns:
        *code*: :class:`sqlalchemy.types.Unicode`
            The plant code

        *acc_type*: :class:`bauble.types.Enum`
            The accession type

            Possible values:
                * Plant: Whole plant

                * Seed/Spore: Seed or Spore

                * Vegetative Part: Vegetative Part

                * Tissue Culture: Tissue culture

                * Other: Other, probably see notes for more information

                * None: no information, unknown

        *accession_id*: :class:`sqlalchemy.types.Integer`
            Required.

        *location_id*: :class:`sqlalchemy.types.Integer`
            Required.

    :Properties:
        *accession*:
            The accession for this plant.
        *location*:
            The location for this plant.
        *notes*:
            Thoe notes for this plant.

    :Constraints:
        The combination of code and accession_id must be unique.
    """
    __tablename__ = 'plant'
    __table_args__ = (UniqueConstraint('code', 'accession_id'), {})
    __mapper_args__ = {'order_by': ['plant.accession_id', 'plant.code']}

    # columns
    code = Column(Unicode(6), nullable=False)
    acc_type = Column(types.Enum(values=acc_type_values.keys(),
                                 translations=acc_type_values),
                      default=None)
    memorial = Column(Boolean, default=False)
    quantity = Column(Integer, autoincrement=False, nullable=False)

    accession_id = Column(Integer, ForeignKey('accession.id'), nullable=False)
    location_id = Column(Integer, ForeignKey('location.id'), nullable=False)

    propagations = relation('Propagation', cascade='all, delete-orphan',
                            single_parent=True,
                            secondary=PlantPropagation.__table__,
                            backref=backref('plant', uselist=False))

    _delimiter = None

    @classmethod
    def get_delimiter(cls, refresh=False):
        """
        Get the plant delimiter from the BaubleMeta table.

        The delimiter is cached the first time it is retrieved.  To refresh
        the delimiter from the database call with refresh=True.

        """
        return default_plant_delimiter
        # TODO: we need to hook our per database settings table back up
        #
        # if cls._delimiter is None or refresh:
        #     cls._delimiter = meta.get_default(plant_delimiter_key,
        #                         default_plant_delimiter).value
        # return cls._delimiter

    def _get_delimiter(self):
        return Plant.get_delimiter()
    delimiter = property(lambda self: self._get_delimiter())


    def __str__(self):
        return "%s%s%s" % (self.accession, self.delimiter, self.code)

    def json(self, pick=None):
        d = super().json()
        d['changes'] = [change.json() for change in self.changes]
        return d


    def duplicate(self, code=None, session=None):
        """
        Return a Plant that is a duplicate of this Plant with attached
        notes, changes and propagations.
        """
        plant = Plant()
        if not session:
            session = object_session(self)
            if session:
                session.add(plant)

        ignore = ('id', 'changes', 'notes', 'propagations')
        properties = filter(lambda p: p.key not in ignore,
                            object_mapper(self).iterate_properties)
        for prop in properties:
            setattr(plant, prop.key, getattr(self, prop.key))
        plant.code = code

        # duplicate notes
        for note in self.notes:
            new_note = PlantNote()
            for prop in object_mapper(note).iterate_properties:
                setattr(new_note, prop.key, getattr(note, prop.key))
            new_note.id = None
            new_note.plant = plant

        # duplicate changes
        for change in self.changes:
            new_change = PlantChange()
            for prop in object_mapper(change).iterate_properties:
                setattr(new_change, prop.key, getattr(change, prop.key))
            new_change.id = None
            new_change.plant = plant

        # duplicate propagations
        for propagation in self.propagations:
            new_propagation = PlantPropagation()
            for prop in object_mapper(propagation).iterate_properties:
                setattr(new_propagation, prop.key,
                        getattr(propagation, prop.key))
            new_propagation.id = None
            new_propagation.plant = plant
        return plant


    def markup(self):
        #return "%s.%s" % (self.accession, self.plant_id)
        # FIXME: this makes expanding accessions look ugly with too many
        # plant names around but makes expanding the location essential
        # or you don't know what plants you are looking at
        return "%s%s%s (%s)" % (self.accession, self.delimiter, self.code,
                                self.accession.taxon_str(markup=True))



# setup the search mapper
mapper_search = search.get_strategy('MapperSearch')
mapper_search.add_meta(('plants', 'plant'), Plant, ['code'])
#search.add_strategy(PlantSearch)
