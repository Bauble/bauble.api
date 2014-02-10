#!/usr/bin/env python

import getpass
import sys

import bauble
import bauble.i18n
import bauble.db as db
from bauble.model import User

email = "admin@bauble.io"
password = sys.argv[1] if len(sys.argv) > 1 else getpass.getpass("New password: ")

session = db.Session()
user = session.query(User).filter_by(email=email).first()
user.password = password
session.commit()
