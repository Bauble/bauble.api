from sqlalchemy import Column, Boolean, String, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref

from bauble.model import SystemModel
import bauble.types as types


class Invitation(SystemModel):

    email = Column(String, unique=True, nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    token_expiration = Column(types.DateTime)
    date_sent = Column(types.DateTime, nullable=False)
    message = Column(String)
    accepted = Column(Boolean)

    invited_by_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    invited_by = relationship('User', uselist=False,
                              backref=backref('invitations',
                                              cascade="all, delete-orphan"))

    organization_id = Column(Integer, ForeignKey('organization.id'), nullable=False)
    organization = relationship('Organization', uselist=False,
                                backref=backref('invitations',
                                                cascade="all, delete-orphan",))
