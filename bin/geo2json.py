#!/usr/bin/env python

import csv
import json
import sys


filename = sys.argv[1]
f = open(filename, newline='')

rows = []

# find a row in the tree with the matching id
def find(rows, row_id):
    for row in rows:
        if row['id'] == row_id:
            return row
        elif 'children' in row:
            found = find(row['children'], row_id)
            if(found):
                return found


for line in csv.DictReader(f):
    row_id = line['id']
    if line['parent_id'] != '':
        parent = find(rows, line['parent_id'])
        if 'children' not in parent:
            parent['children'] = [line]
        else:
            parent['children'].append(line)
    else:
        rows.append(line)

json.dump(rows, sys.stdout)
#print(rows)
