#!/usr/bin/env python

import getpass
import sys

import bauble
import bauble.i18n
import bauble.db as db
from bauble.model import User

username = "admin"
password = sys.argv[1] if len(sys.argv)>1 else getpass.getpass("New password: ")

session = db.connect()
user = session.query(User).filter_by(username=username).first()
user.set_password(password)
session.commit()
