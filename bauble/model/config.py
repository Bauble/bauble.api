#
# Config table definition
#
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


def get(key, session):
    return Config.get(key, session)


def set(key, value, session):
    return Config(key, value, session)


class Config(db.Base):
    __tablename__ = "config"
    __mapper_args__ = {'order_by': ['key']}

    key = Column(String, nullable=False, index=True, unique=True)
    value = Column(String)
    #family_id = Column(Integer, ForeignKey('family.id'), nullable=False)
    #family = relation('Family', backref=backref('genera', cascade='all,delete-orphan'))

    # TODO: see about using relationships across schema boundaries:
    # http://docs.sqlalchemy.org/en/rel_0_8/dialects/postgresql.html#remote-cross-schema-table-introspection
    user_id = Column(Integer, ForeignKey('user.id'))

    @staticmethod
    def get(key, session):
        config = session.query(Config).filter_by(key=key).first()
        return config.value if config else None

    @staticmethod
    def set(key, value, session):
        config = session.query(Config).filter_by(key=key).first()
        if config:
            config.value = value
        else:
            config = Config(key=key, value=value)
            session.add(session)
