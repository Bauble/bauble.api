from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.orm.session import object_session
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.associationproxy import association_proxy

import bauble
import bauble.db as db
#import bauble.utils as utils
#from bauble.utils.log import debug
#import bauble.utils.web as web
import bauble.types as types
import bauble.search as search

class User(db.Base):
    username = Column(String)
    fullname = Column(String)
    title = Column(String)
    email = Column(String)
    organization = Column(String)