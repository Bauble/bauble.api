
from email.mime.text import MIMEText
import os
import smtplib

import bauble



def send(to_email, subject, body):
    use_ssl = os.environ.get("BAUBLE_SMTP_USE_SSL", "false")
    host = os.environ.get("BAUBLE_SMTP_HOST", "")
    port = os.environ.get("BAUBLE_SMTP_PORT", 0)
    user = os.environ.get("BAUBLE_SMTP_USERNAME", None)
    password = os.environ.get("BAUBLE_SMTP_PASSWORD", None)
    support_email = os.environ.get("BAUBLE_SUPPORT_EMAIL", "support@bauble.io")

    SMTP = smtplib.SMTP_SSL if use_ssl or use_ssl.lower() == "true" else smtplib.SMTP

    # **************************************************
    # don't send the email if we're running the tests
    # **************************************************
    if os.environ.get("BAUBLE_TEST", "false") == "true":
        return

    timeout = 10  # 10 second timeout for smtp connection
    message = MIMEText(body, 'plain')
    message['subject'] = subject
    message['reply-to'] = support_email
    with SMTP(host, port, timeout=timeout) as smtp:
        smtp.login(user, password)
        smtp.send_message(message, support_email, to_email)



def send_template(to_email, subject, template_name, mappings):
    template_file = os.path.join(bauble.__path__[0], 'templates', template_name)
    body = open(template_file).read().format_map(mappings)
    send(to_email, subject, body)
