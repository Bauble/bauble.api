
import random
import string

import bauble.db as db

def random_str(length=10, letters=string.ascii_lowercase):
    return "".join([random.choice(letters) for i in range(length)])

def org_session(session, org):
    #session.add(org)
    try:
        schema = org.pg_schema
    except:
        session.add(org)
        schema = org.pg_schema
    db.set_session_schema(session, schema)
    return session
