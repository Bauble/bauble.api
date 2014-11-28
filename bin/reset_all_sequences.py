#!/usr/bin/env python

import operator as op
import os
import psycopg2
import sqlalchemy as sa

db_url = os.environ.get('BAUBLE_DB_URL')

if db_url is None:
    print("** Error: BAUBLE_DB_URL is not defined")
    exit(1)


from bauble.model import Model

col_filter = lambda c: isinstance(c.type, sa.Integer) and c.autoincrement \
    and len(c.foreign_keys) == 0 \
    and (c.default is None or (isinstance(c.default, sa.schema.Sequence) and
                               c.default.optional))

sequences = []
for table in Model.metadata.sorted_tables:
    for column in filter(col_filter, table.columns):
        sequence_name = '{}_{}_seq'.format(table.name, column.name)
        sequences.append((table.name, column.name, sequence_name))


seq_reset_stmt = "SELECT pg_catalog.setval(pg_get_serial_sequence('{table}', '{column}'), (SELECT MAX({column}) FROM {table})+1);"

with psycopg2.connect(db_url) as conn:
    with conn.cursor() as cursor:
        # get all the organization schema
        cursor.execute('select pg_schema from organization;')
        for schema in map(op.itemgetter(0), cursor.fetchall()):
            print('schema: ', schema)
            cursor.execute('set search_path to {},public;'.format(schema))
            for table, column, sequence in sequences:
                cursor.execute('begin;')
                try:
                    stmt = seq_reset_stmt.format(table=table, column=column,
                                                 sequence=sequence)
                    cursor.execute(stmt)
                except Exception as exc:
                    print("Could not reset {} on schema {}".format(sequence, schema))
                    cursor.execute('rollback;')
                    print(exc)
                else:
                    cursor.execute('commit;')
