#
# source.py
#
from sqlalchemy import *
from sqlalchemy.orm import *

import bauble
import bauble.i18n
import bauble.db as db
from bauble.model import Model
from bauble.model.geography import Geography
#import bauble.utils as utils
import bauble.types as types
#from bauble.utils.log import debug
import bauble.search as search

def coll_markup_func(coll):
    acc = coll.source.accession
    safe = utils.xml_safe_utf8
    return '%s - <small>%s</small>' %  \
        (safe(acc), safe(acc.taxon_str())), safe(coll)


class Source(Model):
    """
    """
    __tablename__ = 'source'
    sources_code = Column(Unicode(32))

    accession_id = Column(Integer, ForeignKey('accession.id'), unique=True)

    source_detail_id = Column(Integer, ForeignKey('source_detail.id'))
    source_detail = relation('SourceDetail', uselist=False,
                             backref=backref('sources',
                                             cascade='all, delete-orphan'))

    collection = relation('Collection', uselist=False,
                          cascade='all, delete-orphan',
                          backref=backref('source', uselist=False))

    # Relation to a propagation that is specific to this Source and
    # not attached to a Plant.
    propagation_id = Column(Integer, ForeignKey('propagation.id'))
    propagation = relationship("Propagation", foreign_keys=propagation_id,
                               cascade='all, delete-orphan', single_parent=True,
                               backref=backref('source', uselist=False))

    # relation to a Propagation that already exists and is attached
    # to a Plant
    plant_propagation_id = Column(Integer, ForeignKey('plant_prop.id'))
    plant_propagation = relationship("PlantPropagation", foreign_keys=plant_propagation_id,
                                     uselist=False)




source_type_values = {'Expedition': _('Expedition'),
                      'GeneBank': _('Gene Bank'),
                      'BG': _('Botanic Garden or Arboretum'),
                      'Research/FieldStation': _('Research/Field Station'),
                      'Staff': _('Staff member'),
                      'UniversityDepartment': _('University Department'),
                      'Club': _('Horticultural Association/Garden Club'),
                      'MunicipalDepartment': _('Municipal department'),
                      'Commercial': _('Nursery/Commercial'),
                      'Individual': _('Individual'),
                      'Other': _('Other'),
                      'Unknown': _('Unknown'),
                      None: ''}


class SourceDetail(Model):
    __tablename__ = 'source_detail'
    __mapper_args__ = {'order_by': 'name'}

    name = Column(Unicode(75), unique=True)
    description = Column(UnicodeText)
    source_type = Column(types.Enum(values=source_type_values.keys(),
                                    translations=source_type_values),
                         default=None)

    def __str__(self):
        return self.name if self.name else ""



# TODO: should provide a collection type: alcohol, bark, boxed,
# cytological, fruit, illustration, image, other, packet, pollen,
# print, reference, seed, sheet, slide, transparency, vertical,
# wood.....see HISPID standard, in general need to be more herbarium
# aware

# TODO: create a DMS column type to hold latitude and longitude,
# should probably store the DMS data as a string in decimal degrees
class Collection(Model):
    """
    :Table name: collection

    :Columns:
            *collector*: :class:`sqlalchemy.types.Unicode`

            *collectors_code*: :class:`sqlalchemy.types.Unicode`

            *date*: :class:`sqlalchemy.types.Date`

            *locale*: :class:`sqlalchemy.types.UnicodeText`

            *latitude*: :class:`sqlalchemy.types.Float`

            *longitude*: :class:`sqlalchemy.types.Float`

            *gps_datum*: :class:`sqlalchemy.types.Unicode`

            *geo_accy*: :class:`sqlalchemy.types.Float`

            *elevation*: :class:`sqlalchemy.types.Float`

            *elevation_accy*: :class:`sqlalchemy.types.Float`

            *habitat*: :class:`sqlalchemy.types.UnicodeText`

            *geography_id*: :class:`sqlalchemy.types.Integer`

            *notes*: :class:`sqlalchemy.types.UnicodeText`

            *accession_id*: :class:`sqlalchemy.types.Integer`


    :Properties:


    :Constraints:
    """
    __tablename__ = 'collection'

    # columns
    collector = Column(Unicode(64))
    collectors_code = Column(Unicode(50))
    date = Column(types.Date)
    locale = Column(UnicodeText, nullable=False)
    latitude = Column(Unicode(15))
    longitude = Column(Unicode(15))
    gps_datum = Column(Unicode(32))
    geo_accy = Column(Float)
    elevation = Column(Float)
    elevation_accy = Column(Float)
    habitat = Column(UnicodeText)
    notes = Column(UnicodeText)

    geography_id = Column(Integer, ForeignKey('geography.id'))
    region = relation(Geography, uselist=False)

    source_id = Column(Integer, ForeignKey('source.id'), unique=True)

    def __str__(self):
        return _('Collection at %s') % (self.locale or repr(self))




# setup the search mapper
mapper_search = search.get_strategy('MapperSearch')
mapper_search.add_meta(('contacts', 'contact', 'contacts', 'person', 'org',
                        'source'), SourceDetail, ['name'])
mapper_search.add_meta(('collections', 'collection', 'col', 'coll'),
                       Collection, ['locale'])
