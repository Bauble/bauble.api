from sqlalchemy import *
from sqlalchemy.orm import *
import sqlalchemy.event as event

import bauble
import bauble.db as db
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
            d['date_approved'] = str(self.date_approved)

        if depth > 1:
            d['users'] = [user.json(depth=depth-1) for user in self.users]
            d['owners'] = [owner.json(depth=depth-1) for owner in self.owners]

        return d


    def admin_json(self, depth=1):
        d = self.json()
        d['date_suspended'] = str(self.date_suspended) if self.date_suspended else None
        d['date_created'] = str(self.date_created) if self.date_created else None
        d['date_approved'] = str(self.date_approved) if self.date_approved else None
        d['pg_schema'] = self.pg_schema
        return d


@event.listens_for(Organization, 'before_insert')
def before_insert(mapper, connection, organization):
    # new organiations require at least one owner
    if(len(organization.owners) < 1):
        raise ValueError("An owner user is required for new organizations")


@event.listens_for(Organization, 'after_insert')
def after_insert(mapper, connection, organization):
    org_table = object_mapper(organization).local_table
    schema_name = db.create_unique_schema()
    stmt = org_table.update().where(org_table.c.id==organization.id)\
        .values(pg_schema=schema_name)
    connection.execute(stmt)


@event.listens_for(Organization, 'after_delete')
def after_delete(mapper, connection, organization):
    # TODO: delete the schema associated with the organization
    pass
