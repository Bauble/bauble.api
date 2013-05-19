from sqlalchemy import *
from sqlalchemy.orm import *

import bauble
import bauble.db as db
#import bauble.utils as utils
#from bauble.utils.log import debug
#import bauble.utils.web as web
import bauble.types as types
import bauble.search as search

class User(db.SystemBase):
    __tablename__ = 'user'

    username = Column(String, nullable=False, unique=True)
    fullname = Column(String)
    title = Column(String)
    email = Column(String)
    password = Column(String)

    is_sysadmin = Column(Boolean)

    is_org_owner = Column(Boolean)
    organization_id = Column(Integer, ForeignKey('organization.id'))
