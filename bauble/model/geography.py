#
# geography.py
#
from operator import itemgetter

from sqlalchemy import *
from sqlalchemy.orm import *

import bauble
import bauble.db as db
from bauble.model import Model
import bauble.search as search
#from bauble.utils.log import debug


def get_taxa_in_geography(geo):#, session=None):
    """
    Return all the Taxon that have distribution in geo
    """
    session = object_session(geo)
    if not session:
        ValueError('get_taxa_in_geography(): geography is not in a session')

    # get all the geography children under geo
    from bauble.model import TaxonDistribution, Taxon
    # get the children of geo
    geo_table = geo.__table__
    master_ids = set([geo.id])

    # populate master_ids with all the geography ids that represent
    # the children of particular geography id
    def get_geography_children(parent_id):
        stmt = select([geo_table.c.id], geo_table.c.parent_id == parent_id)
        kids = [r[0] for r in db.engine.execute(stmt).fetchall()]
        for kid in kids:
            grand_kids = get_geography_children(kid)
            master_ids.update(grand_kids)
        return kids
    geokids = get_geography_children(geo.id)
    master_ids.update(geokids)
    q = session.query(Taxon).join(TaxonDistribution).\
        filter(TaxonDistribution.geography_id.in_(master_ids))
    return list(q)


class Geography(Model):
    """
    Represents a geography unit.

    :Table name: geography

    :Columns:
        *name*:

        *tdwg_code*:

        *iso_code*:

        *parent_id*:

    :Properties:
        *children*:

    :Constraints:
    """
    __tablename__ = 'geography'

    # columns
    name = Column(Unicode(255), nullable=False)
    tdwg_code = Column(String(6))
    iso_code = Column(String(7))
    parent_id = Column(Integer, ForeignKey('geography.id'))


    def __str__(self):
        return self.name


    def json(self, depth=1):
        d = dict(ref="/geography/" + str(self.id))
        if depth > 0:
            d['name'] = self.name
            d['parent'] = self.parent.json(depth=depth - 1) if self.parent else ''
            d['str'] = str(self)

        if depth > 1:
            d['tdwg_code'] = self.tdwg_code
            d['iso_code'] = self.iso_code

        return d




# late bindings
Geography.children = relation(Geography,
                              primaryjoin=Geography.parent_id==Geography.id,
                              cascade='all',
                              backref=backref("parent",
                                    remote_side=[Geography.__table__.c.id]),
                              order_by=[Geography.name])

# setup search mapper
mapper_search = search.get_strategy('MapperSearch')
mapper_search.add_meta(('geography', 'geo'), Geography, ['name'])
