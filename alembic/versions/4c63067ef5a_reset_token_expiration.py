"""reset token expiration

Revision ID: 4c63067ef5a
Revises: 5465d2b606d
Create Date: 2014-04-06 11:12:35.160180

"""

# revision identifiers, used by Alembic.
revision = '4c63067ef5a'
down_revision = '5465d2b606d'

from alembic import context, op
import sqlalchemy as sa


def upgrade():
    stmt = 'SELECT column_name FROM information_schema.columns WHERE table_name=\'user\' and column_name=\'password_reset_token_expiration\';'
    has_column = context.get_context().bind.execute(stmt).scalar()
    if not has_column:
        op.add_column('user', sa.Column('password_reset_token_expiration', sa.DateTime))



def downgrade():
    op.drop_column('user', 'password_reset_token')
