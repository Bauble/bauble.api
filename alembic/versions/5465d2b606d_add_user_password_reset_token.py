"""add user.password_reset_token

Revision ID: 5465d2b606d
Revises: None
Create Date: 2014-04-04 09:14:09.714088

"""

# revision identifiers, used by Alembic.
revision = '5465d2b606d'
down_revision = None

import alembic
from alembic import op, context
import sqlalchemy as sa


def upgrade():
    stmt = 'SELECT column_name FROM information_schema.columns WHERE table_name=\'user\' and column_name=\'password_reset_token\';'
    has_column = context.get_context().bind.execute(stmt).scalar()
    if not has_column:
        op.add_column('user', sa.Column('password_reset_token', sa.String))


def downgrade():
    op.drop_column('user', 'password_reset_token')
