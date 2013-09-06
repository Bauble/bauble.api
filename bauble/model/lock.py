from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.orm.session import object_session
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.associationproxy import association_proxy

import bauble
import bauble.db as db
import bauble.types as types
import bauble.search as search

class Lock(db.Base):
    __tablename__ = 'lock'

    table_name = String(32, nullable=False, index=True)
    table_id = Integer(nullable=False, index=True)
    lock_created = Column(types.DateTime, nullable=False)
    locked_by = String(nullable=False)
    locked_released = Column(types.DateTime, nullable=False)
