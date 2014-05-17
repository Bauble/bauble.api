import csv
from decimal import Decimal
import os
import re
import sys

if len(sys.argv) != 2:
    print("Usage: csv_to_sql.py <csvfile>")
    sys.exit(1)

filename = sys.argv[1]
table_name = os.path.splitext(os.path.basename(filename))[0]



rx = re.compile('(?P<quote>[\'"])(.*?)(?P=quote)', re.DOTALL)

def format(value):
    try:
        return str(Decimal(value))
    except:
        # remove any embedded quotes in the string
        value = rx.sub('\g<2>', value)
        #print(value)
        if value in ('', "''", '""'):
            return 'DEFAULT'
        #return value
        return "'{0}'".format(value)


reader = csv.reader(open(filename, newline='', encoding='utf-8',))
print('insert into {0} ({1}) values'.format(table_name, ','.join(reader.__next__())))
values = []
for row in reader:
    values.append("({0})".format(','.join([format(value) for value in row])))

# import_file = open(filename, newline='', encoding='utf-8')
# header = import_file.readline().strip()
# print('insert into {0} ({1}) values'.format(table_name, header))

# values = []
# for row in import_file:
#     values.append("({0})".format(','.join([format(value) for value in row.strip().split(',')])))

print(',\n'.join(values) + ';')
