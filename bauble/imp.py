import csv

import bauble
import bauble.db as db
from bauble.model import Model
import bauble.utils as utils

QUOTE_STYLE = csv.QUOTE_MINIMAL
QUOTE_CHAR = '"'

def from_csv(filemap, schema):
    """
    Import a list of files files to tables where <filemap> is a dict of
    tablenames to file names.

    schema: the name of the schema for the tables in filemap
    """
    session = db.Session()
    db.set_session_schema(session, schema)

    table_name = ''
    current_row = []
    try:
        # import the files in order of their dependency
        sorted_tables = list(filter(lambda t: t.name in filemap, Model.metadata.sorted_tables))

        for table in sorted_tables:
            print('importing into {} ...'.format(table_name))
            table_name = table.name  # mostly for error reporting
            if isinstance(filemap[table_name], str):
                import_file = open(filemap[table_name], newline='', encoding='utf-8')
            else:
                import_file = filemap[table_name]

            reader = csv.DictReader(import_file, quotechar=QUOTE_CHAR,
                                    quoting=QUOTE_STYLE)
            rows = []
            for row in reader:
                current_row = row
                rows.append({key: value if value != "" else None
                             for key, value in row.items()})
            print('importing {} rows in to {}'.format(len(rows), table_name))
            session.execute(table.insert(), rows)

        session.commit()

        # reset the sequence
        for table in sorted_tables:
            for col in table.c:
                utils.reset_sequence(col)
    except:
        print("Error importing into ", table_name)
        print('current_row: ', current_row)
        session.rollback()
        raise
    finally:
        session.close()
