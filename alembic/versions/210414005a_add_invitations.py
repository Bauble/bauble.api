"""add invitations

Revision ID: 210414005a
Revises: 4c63067ef5a
Create Date: 2014-04-06 14:28:04.421336

"""

# revision identifiers, used by Alembic.
revision = '210414005a'
down_revision = '4c63067ef5a'

from alembic import context, op
from sqlalchemy import Column, Boolean, String, Integer, DateTime, ForeignKey, func


def upgrade():
    stmt = 'SELECT column_name FROM information_schema.columns WHERE table_name=\'user\' and column_name=\'password_reset_token\';'
    stmt = 'select table_name from information_schema.tables where table_name=\'invitation\''
    has_table = context.get_context().bind.execute(stmt).scalar()
    if has_table:
        return

    op.create_table(
        'invitation',
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('_created', DateTime(True), default=func.now()),
        Column('_last_updated', DateTime(True), default=func.now(),
               onupdate=func.now()),
        Column('email', String, nullable=False),
        Column('token', String, unique=True, index=True, nullable=False),
        Column('token_expiration', DateTime),
        Column('date_sent', DateTime, nullable=False),
        Column('message', String),
        Column('accepted', Boolean, default=False),
        Column('organization_id', Integer, ForeignKey('organization.id')),
        Column('invited_by_id', Integer, ForeignKey('user.id')),
    )


def downgrade():
    op.drop_table('invitation')
