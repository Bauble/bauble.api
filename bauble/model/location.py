#
# location.py
#
from sqlalchemy import *
from sqlalchemy.orm import *

import bauble.db as db
from bauble.model import Model
import bauble.search as search


def loc_markup_func(location):
    if location.description is not None:
        return utils.xml_safe(str(location)), \
            utils.xml_safe(str(location.description))
    else:
        return utils.xml_safe(str(location))


class Location(Model):
    """
    :Table name: location

    :Columns:
        *name*:

        *description*:

    :Relation:
        *plants*:

    """
    __tablename__ = 'location'
    __mapper_args__ = {'order_by': 'name'}

    # columns
    # refers to beds by unique codes
    code = Column(Unicode(10), unique=True, nullable=False)
    name = Column(Unicode(64))
    description = Column(UnicodeText)

    # relations
    plants = relation('Plant', backref=backref('location', uselist=False))

    def __str__(self):
        if self.name:
            return '(%s) %s' % (self.code, self.name)
        else:
            return str(self.code)


    def json(self, depth=1):
        d = dict(ref="/location/" + str(self.id))
        if depth > 0:
            d['id'] = self.id
            d['code'] = self.code
            d['name'] = self.name
            d['str'] = str(self)
        if depth > 1:
            d['description'] = self.description

        return d


# setup the search mapper
mapper_search = search.get_strategy('MapperSearch')
mapper_search.add_meta(('locations', 'location', 'loc'), Location, ['name', 'code'])
