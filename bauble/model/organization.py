from sqlalchemy import *
from sqlalchemy.orm import *
import sqlalchemy.event as event

import bauble
import bauble.db as db
#import bauble.utils as utils
#from bauble.utils.log import debug
#import bauble.utils.web as web
import bauble.types as types

class Organization(db.SystemBase):
    __tablename__ = 'organization'

    name = Column(String)
    short_name = Column(String)

    # pg_user and pg_schema should be the same, these are create automatically
    # when a a new account is created
    pg_user = Column(String, unique=True)
    pg_schema = Column(String, unique=True)

    # TODO: do we need this????
    #pg_user = Column(String, unique=True)

    owners = relationship('User', primaryjoin="and_("\
                              "Organization.id==User.organization_id,"\
                              "User.is_org_owner==True)")
    admins = relationship('User', primaryjoin="and_("\
                              "Organization.id==User.organization_id,"\
                              "or_(User.is_org_owner==True, User.is_org_admin)==True)")
    users = relationship('User', cascade="all, delete-orphan",
                         backref=backref("organization", uselist=False))

    date_approved = Column(types.Date)
    date_created = Column(types.Date, default=func.now())
    date_suspended = Column(types.Date)


    def get_ref(self):
        return "/organization/" + str(self.id) if self.id is not None else None;


    def json(self, depth=1):
        d = dict()
        if self.id:
            d['ref'] = self.get_ref()

        if depth > 0:
            d['name'] = self.name
            d['short_name'] = self.short_name

        if depth > 1:
            d['users'] = [user.json(depth=depth-1) for user in self.users]
            d['owners'] = [owner.json(depth=depth-1) for owner in self.owners]

        return d


def before_insert(mapper, connection, organization):
    # new organiations require at least one owner
    if(len(organization.owners) < 1):
        raise ValueError("An owner user is required for new organizations")


event.listen(Organization, "before_insert", before_insert)
