
import bcrypt
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

    # system permissions
    is_sysadmin = Column(Boolean)
    is_org_owner = Column(Boolean)
    is_org_admin = Column(Boolean)

    organization_id = Column(Integer, ForeignKey('organization.id'))

    # TODO: This should probably be made into a property so that
    # passwords are always hashed
    def set_password(self, password):
        """Encrypt and set the password.
        """
        import bcrypt
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        self.password = hashed.decode("utf-8")


    def get_ref(self):
        return "/user/" + str(self.id) if self.id is not None else None;


    def json(self, depth=1):
        """Return a dict/JSON representation of this User.
        """
        d = dict()
        if self.id:
            d['ref'] = self.get_ref()

        if depth > 0:
            d['username'] = self.username
            d['fullname'] = self.fullname
            d['title'] = self.title
            d['email'] = self.email
            d['is_sysadmin'] = self.is_sysadmin
            d['is_org_owner'] = self.is_org_owner
            d['is_org_admin'] = self.is_org_admin

        if depth > 1:
            d['organization'] = self.organization.json(depth-1) \
                if self.organization else {}

        return d
