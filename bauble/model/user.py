
import bcrypt
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.ext.hybrid import Comparator, hybrid_property
from sqlalchemy.orm import *

import bauble
import bauble.db as db
#import bauble.utils as utils
#from bauble.utils.log import debug
#import bauble.utils.web as web
import bauble.types as types


class EncryptedPassword(Comparator):
    """
    Comparator to handle encrypted passwords.
    """

    def __init__(self, password):
        self._password = password


    def operate(self, op, other):
        if not isinstance(other, EncryptedPassword):
            encode = lambda s: s.encode("utf-8") if s else "".encode("utf-8")
            other = bcrypt.hashpw(encode(other), encode(self._password)).decode('utf-8')
        return op(self._password, other)


    def __clause_element__(self):
        return self._password


    def __str__(self):
        return self._password



class User(db.SystemBase):

    def __init__(self, *args, password=None, **kwargs):
        self.password = password
        return super().__init__(*args, **kwargs)

    __tablename__ = 'user'

    username = Column(String, nullable=False, unique=True)
    fullname = Column(String)
    title = Column(String)
    email = Column(String)
    _password = Column('password', String, nullable=False)

    # system permissions
    is_sysadmin = Column(Boolean)
    is_org_owner = Column(Boolean)
    is_org_admin = Column(Boolean)

    last_accessed = Column(types.DateTime)
    date_suspended = Column(types.Date)

    # the user->organization relationship is created as a backref on the
    # organization object
    organization_id = Column(Integer, ForeignKey('organization.id'))


    @hybrid_property
    def password(self):
        return EncryptedPassword(self._password)


    @password.setter
    def set_password(self, password):
        """Encrypt and set the password.
        """
        self._password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode('utf-8')


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
