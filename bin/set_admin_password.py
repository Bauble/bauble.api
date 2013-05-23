#!/usr/bin/env python

import getpass

import bauble
import bauble.i18n
import bauble.db as db
from bauble.model import User

username = "admin"
old_password = getpass.getpass("Old password: ")
new_password = getpass.getpass("New password: ")

session = db.connect()
user = session.query(User).filter_by(username=username).first()
user.set_password(new_password)
session.commit()
