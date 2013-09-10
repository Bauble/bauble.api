import csv
import os
from tempfile import mkstemp

from bauble.imp import from_csv

def test_import():
    fields = ["family"]
    family_data = [('SomeFamily',), ('AnotherFamily',)]
    file_handle, filename = mkstemp()
    print('filename: ', filename)
    csv_writer = csv.writer(os.fdopen(file_handle, "w"), fields)
    csv_writer.writerow(fields)
    for row in family_data:
        print('row: ', row)
        csv_writer.writerow(row)

    from_csv({'family': filename})
    assert False
