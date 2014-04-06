"""reset token expiration

Revision ID: 4c63067ef5a
Revises: 5465d2b606d
Create Date: 2014-04-06 11:12:35.160180

"""

# revision identifiers, used by Alembic.
revision = '4c63067ef5a'
down_revision = '5465d2b606d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('password_reset_token_expiration', sa.DateTime))



def downgrade():
    op.drop_column('user', 'password_reset_token')
