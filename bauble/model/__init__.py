import json

from sqlalchemy import Column, Integer, func, inspect
from bauble.types import DateTime
from sqlalchemy.ext.declarative import declarative_base, declared_attr, DeclarativeMeta

class ModelBase:

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column('id', Integer, primary_key=True, autoincrement=True)
    _created = Column('_created', DateTime(True), default=func.now())
    _last_updated = Column('_last_updated', DateTime(True), default=func.now(),
                           onupdate=func.now())

    never = set()
    omit = set()

    def __new__(cls, *args, **kwargs):
        # TODO: we should build the omit once when the class is declared rather
        # than evertime it's instantiated

        cls.omit = cls.omit | {key for key in inspect(cls).attrs.keys() if key.startswith('_') or key in cls.never}
        return super().__new__(cls)


    def json(self, pick=None):
        # TODO: we need to get all attributes, not just columns
        columns = set(inspect(self).mapper.columns.keys())
        if pick:
            columns = columns.intersection(pick).difference(self.never)
        else:
            columns = columns.difference(self.omit)

        d = {col: getattr(self, col) for col in columns}
        if (pick and 'str' in pick) or 'str' not in self.omit:
            d['str'] = str(self)
        return d



Model = declarative_base(cls=ModelBase)

import bauble.model.meta
from bauble.model.family import Family, FamilyNote, FamilySynonym
from bauble.model.genus import Genus
from bauble.model.taxon import Taxon
from bauble.model.accession import Accession
from bauble.model.plant import Plant
from bauble.model.location import Location
from bauble.model.source import Source, SourceDetail, Collection
from bauble.model.geography import Geography

from bauble.model.user import User
from bauble.model.organization import Organization
