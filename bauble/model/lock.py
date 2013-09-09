from datetime import datetime, timedelta

from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.orm.session import object_session
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.associationproxy import association_proxy

import bauble
import bauble.db as db
from bauble.model.user import User
import bauble.types as types
import bauble.search as search

def default_expiration():
    return datetime.utcnow() + timedelta(days=90)

class Lock(db.Base):
    __tablename__ = 'lock'

    resource = Column(String(32), nullable=False, index=True)

    date_created = Column(types.DateTime, nullable=False, default=func.now())

    # a future datetime when this lock automatically expires
    date_expires = Column(types.DateTime, nullable=False, default=default_expiration)

    # a past datetime when this lock was released, either expired or delete
    date_released = Column(types.DateTime)

    # this should be a
    user_id = Column(Integer, ForeignKey(User.id, schema="public"), nullable=False)
    user = relationship(User, backref="locks")

    def json(self, depth=1):
        d = dict(resource=self.resource)
        if(depth>0):
            d['date_created'] = str(self.date_created)
            d['data_released'] = str(self.date_released) if self.date_released else ""
            d['user'] = self.user.json(depth=depth - 1)
