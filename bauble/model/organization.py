from sqlalchemy import *
from sqlalchemy.orm import *
import sqlalchemy.event as event

import bauble
import bauble.db as db
import bauble.types as types
from bauble.model import SystemModel

class Organization(SystemModel):
    __tablename__ = 'organization'

    name = Column(String)
    short_name = Column(String)

    # pg_user and pg_schema should be the same, these are create automatically
    # when a a new account is created
    pg_user = Column(String, unique=True)
    pg_schema = Column(String, unique=True)

    address = Column(String)
    city = Column(String)
    state = Column(String)
    zip = Column(String)

    owners = relationship('User', cascade='save-update, merge, expunge, refresh-expire',  # cascade='all, delete-orphan',
                          primaryjoin="and_("
                          "Organization.id==User.organization_id,"
                          "User.is_org_owner==True)")
    admins = relationship('User', cascade='save-update, merge, expunge, refresh-expire',  # cascade=None,
                          primaryjoin="and_("
                          "Organization.id==User.organization_id,"
                          "or_(User.is_org_owner==True, User.is_org_admin)==True)")
    users = relationship('User', cascade='save-update, merge, expunge, refresh-expire',
                         primaryjoin=("Organization.id==User.organization_id"),
                         backref=backref("organization", uselist=False), cascade_backrefs=True)

    date_approved = Column(types.Date)
    date_created = Column(types.Date, default=func.now())
    date_suspended = Column(types.Date)


    # def get_ref(self):
    #     return "/organization/" + str(self.id) if self.id is not None else None;


    def __str__(self):
        return str(self.name)


    def json(self, pick=None):
        d = super().json(pick)
        d['owners'] = [owner.id for owner in self.owners]
        d['users'] = [user.id for user in self.users]
        del d['pg_schema']
        del d['pg_user']
        return d

    # def json(self, pick=None):
    #     columns = ['id', 'name', 'short_name', 'date_approved']
    #     d = {column: getattr(self, column) for column in columns
    #          if getattr(self, column)}
    #     d['owners'] = [owner.id for owner in self.owners]
    #     d['users'] = [owner.id for owner in self.users]

    #     return d

    #     d = dict()
    #     if self.id:
    #         d['id'] = self.id


    #     d['name'] = self.name
    #     d['short_name'] = self.short_name
    #     d['date_approved'] = str(self.date_approved)

    #     # if depth > 1:
    #     #     d['users'] = [user.json(depth=depth-1) for user in self.users]
    #     #     d['owners'] = [owner.json(depth=depth-1) for owner in self.owners]

    #     return d


    # def admin_json(self, depth=1):
    #     d = self.json()
    #     d['date_suspended'] = str(self.date_suspended) if self.date_suspended else None
    #     d['date_created'] = str(self.date_created) if self.date_created else None
    #     d['date_approved'] = str(self.date_approved) if self.date_approved else None
    #     d['pg_schema'] = self.pg_schema
    #     return d


    def get_session(self):
        """
        Return a session with this organization's PostgreSQL schema in the db search path.
        """
        session = db.Session();
        org = session.merge(self)
        if not org.pg_schema:
            session.close()
            return None
        db.set_session_schema(session, org.pg_schema)
        return session



@event.listens_for(Organization, 'before_insert')
def before_insert(mapper, connection, organization):
    # new organiations require at least one owner
    if(len(organization.owners) < 1):
        raise ValueError("An owner user is required for new organizations")


@event.listens_for(Organization, 'after_insert')
def after_insert(mapper, connection, organization):
    """
    Create a unique PostgreSQL schema for organization and set it's name on the
    organizations pg_schema field.
    """
    org_table = object_mapper(organization).local_table
    schema_name = db.create_unique_schema()
    stmt = org_table.update().where(org_table.c.id==organization.id)\
        .values(pg_schema=schema_name)
    connection.execute(stmt)


@event.listens_for(Organization, 'after_delete')
def after_delete(mapper, connection, organization):
    """
    Drop the organization's database schema when the organization is deleted.
    """
    connection.execute("drop schema {} cascade;".format(organization.pg_schema))
