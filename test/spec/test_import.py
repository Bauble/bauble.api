import csv
import os
from tempfile import mkstemp

from bauble.imp import from_csv
import test.fixtures as fixtures
from test.fixtures import org

def test_import(org):
    fields = ["family"]
    family_data = [('SomeFamily',), ('AnotherFamily',)]
    file_handle, filename = mkstemp()
    export_file = os.fdopen(file_handle, "w")
    csv_writer = csv.writer(export_file, fields)
    csv_writer.writerow(fields)
    for row in family_data:
        csv_writer.writerow(row)
    export_file.close()
    from_csv({'family': filename}, org.pg_schema)

    session = db.connect()
    db.set_session_schema(org.pg_schema)
    families = session.query(Family)
    assert famililies.count() == 2
    family1 = families.filter_by(family=family_data[0][0]).one()
    assert family1.family == family_data[0][0]
    assert False
