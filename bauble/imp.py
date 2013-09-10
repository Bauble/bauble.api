import csv

import sqlalchemy as sa
import sqlalchemy.orm as orm

import bauble
import bauble.db as db
import bauble.model as model

def from_csv(filemap, schema):
    """
    Import a list of files files to tables where <filemap> is a dict of
    tablenames to file names.

    schema: the name of the schema for the tables in filemap
    """

    # TODO:
    # 1. need to support schemas or even
    # 2. should we support imports to system level tables
    # 3. need to setup a test organization so we can get the schema from it

    session = db.connect()
    db.set_session_schema(session, schema)
    connection = session.connection()
    transaction = connection.begin()

    try:
        # import the files in order of their dependency
        for table in db.metadata.sorted_tables:
            if not table.name in filemap:
                continue

            if isinstance(filemap[table.name], str):
                import_file = open(filemap[table.name], newline='')
            else:
                import_file = filemap[table.name]

            reader = csv.DictReader(import_file)
            session.execute(table.insert(), reader)
        session.commit()
    except:
        session.rollback()
        raise
