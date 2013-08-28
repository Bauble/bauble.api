import os
import sys

#
# TODO: check the permissions on this file and only read it if it's only readable
# by the owner of this process
#

bauble_rcfile=os.path.join(os.environ['HOME'], ".bauble.api")

# read environment variables from the bauble rcfile
if os.path.exists(bauble_rcfile) and os.path.isfile(bauble_rcfile):
    for line in open(bauble_rcfile):
        name, value = line.split('=')
        if isinstance(name, str) and isinstance(value, str):
            os.environ[name.strip()] = str(value).strip()

if 'DATABASE_URL' not in os.environ:
    raise Exception("DATABASE_URL not in environment")
