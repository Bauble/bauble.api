
from email.mime.text import MIMEText
import json
import os
import smtplib
import traceback

import bottle
from bottle import request, response

from bauble.server import app, API_ROOT, parse_accept_header, JSON_MIMETYPE, \
    TEXT_MIMETYPE, enable_cors, parse_auth_header, accept

@app.route(API_ROOT + "/contact", method=['OPTIONS', 'POST'])
def post_contact():

    if(request.method == 'OPTIONS'):
        return {}

    # make sure the content is JSON
    if JSON_MIMETYPE not in request.headers.get("Content-Type"):
        raise bottle.HTTPError('415 Unsupported Media Type',
                               'Expected application/json')

    try:
        data = json.loads(request.body.read().decode('utf-8'))
        msg = MIMEText(data['message'])
        msg["Subject"] = data["subject"]
        msg["From"] = "{name} <{frum}>".format(name=data["name"], frum=data["from"])
        msg["To"] = "contact@bauble.io"
        server = smtplib.SMTP_SSL(os.environ.get('SMTP_SERVER', ''),
                                  os.environ.get('SMTP_PORT', 465))
        server.login(os.environ.get('SMTP_USERNAME', ''),
                     os.environ.get('SMTP_PASSWORD', ''))
        server.send_message(msg)
        server.quit()
    except Exception as exc:
        print(traceback.format_exc())
        #print(exc)  # for logging
        bottle.abort(400, "Email could not be sent")
