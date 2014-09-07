"""create report table

Revision ID: d2c3abb804
Revises: 210414005a
Create Date: 2014-05-25 20:05:53.851881

"""

# revision identifiers, used by Alembic.
revision = 'd2c3abb804'
down_revision = '210414005a'

from alembic import context, op
import sqlalchemy as sa

import bauble.db as db
from bauble.model import Report

def table_exists(table_name, schema):
    result = db.engine.execute("select 1 from information_schema.tables where table_name='{}' and table_schema = '{}';".format(table_name, schema)).first()
    return result is not None


def upgrade():
    # This migration has to run on a live database and can't be used to
    # generate sql statements.
    if context.is_offline_mode():
        raise RuntimeError("This migration script cannot be run in offline mode.")

    # create the report table on all the existing bauble schemas
    stmt = "select schema_name from information_schema.schemata where schema_name like 'bbl_%%';"
    for result in db.engine.execute(stmt):
        schema = result[0]
        if table_exists('report', schema):
            continue

        columns = [c.copy() for c in sa.inspect(Report).columns]
        print("creating table: {}.report".format(schema))
        op.create_table("report", *columns, schema=schema)



def downgrade():
    if context.is_offline_mode():
        raise RuntimeError("This migration script cannot be run in offline mode.")

    # drop the report table on all the existing bauble schemas
    stmt = "select schema_name from information_schema.schemata where schema_name like 'bbl_%%';"
    for result in db.engine.execute(stmt):
        schema = result[0]
        if table_exists('report', schema):
            continue
        print("dropping table: {}.report".format(schema))
        op.drop_table("report", schema=schema)
