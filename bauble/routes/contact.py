
from email.mime.text import MIMEText
import json
import os
import smtplib
import traceback

import bottle
from bottle import request, response

from bauble import app, API_ROOT
import bauble.mimetype as mimetype
from bauble.middleware import *


@app.post(API_ROOT + "/contact")
@accept(mimetype.json)
def post_contact():
    try:
        data = json.loads(request.body.read().decode('utf-8'))
        msg = MIMEText(data['message'])
        msg["Subject"] = data["subject"] if "subject" in data else "Contact Form"
        msg["From"] = "{name} <{email}>".format(name=data["name"], email=data["from"])
        msg["To"] = "contact@bauble.io"
        server = smtplib.SMTP_SSL(os.environ.get('SMTP_SERVER', ''),
                                  os.environ.get('SMTP_PORT', 465))
        server.login(os.environ.get('SMTP_USERNAME', ''),
                     os.environ.get('SMTP_PASSWORD', ''))
        server.send_message(msg)
        server.quit()
    except Exception as exc:
        print(traceback.format_exc())
        bottle.abort(400, "Email could not be sent")
