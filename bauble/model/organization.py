from sqlalchemy import *
from sqlalchemy.orm import *

import bauble
import bauble.db as db
#import bauble.utils as utils
#from bauble.utils.log import debug
#import bauble.utils.web as web
import bauble.types as types

class Organization(db.Base):
    __tablename__ = 'organization'

    name = Column(String)   
    owners = relationship('User')
    users = relationship('User')
