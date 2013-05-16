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
    short_name = Column(String)
    owners = relationship('User')
    users = relationship('User')

    def json(self, depth=1):
        d = dict(ref="/organization/" + str(self.id))
        if(depth > 0):
            d['name'] = self.name
            d['short_name'] = self.short_name

        if(depth > 1):
            d['users'] = [users.json(depth=depth-1) for user in self.users]

        return d
