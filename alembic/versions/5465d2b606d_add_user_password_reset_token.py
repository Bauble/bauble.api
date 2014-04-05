"""add user.password_reset_token

Revision ID: 5465d2b606d
Revises: None
Create Date: 2014-04-04 09:14:09.714088

"""

# revision identifiers, used by Alembic.
revision = '5465d2b606d'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('password_reset_token', sa.String))



def downgrade():
    op.drop_column('user', 'password_reset_token')
