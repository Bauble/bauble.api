"""add invitations

Revision ID: 210414005a
Revises: 4c63067ef5a
Create Date: 2014-04-06 14:28:04.421336

"""

# revision identifiers, used by Alembic.
revision = '210414005a'
down_revision = '4c63067ef5a'

from alembic import context, op
import sqlalchemy as sa

from bauble.model import Invitation


def upgrade():
    stmt = "select table_name from information_schema.tables where table_name='invitation';"
    result = context.execute(stmt)
    if result and result.scalar():
        return

    table = sa.inspect(Invitation).tables[0]
    op.create_table(table.name, *[c.copy() for c in table.columns])



def downgrade():
    op.drop_table('invitation')
