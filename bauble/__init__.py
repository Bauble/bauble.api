import os
import sys

bauble_rcfile=os.path.join(os.environ['HOME'], ".bauble.api")

# read environment variables from the bauble rcfile
if os.path.exists(bauble_rcfile) and os.path.isfile(bauble_rcfile):
    for line in open(bauble_rcfile):
        name, value = line.split('=')
        if isinstance(name, str) and isinstance(value, str):
            os.environ[name.strip()] = str(value).strip()
else:
    raise FileNotFoundError("~/bauble.api does not exist")

if 'DATABASE_URL' not in os.environ:
    raise Exception("DATABASE URL not in environment")
