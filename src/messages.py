import smtplib
from email.mime.text import MIMEText
from string import Template

from twilio.rest import TwilioRestClient

from convenience import settings

def text(to, body):
    sid = settings["RECALL_TWILIO_SID"]
    auth_token = settings["RECALL_TWILIO_AUTH_TOKEN"]
    number = settings["RECALL_TWILIO_PHONE_NUMBER"]
    client = TwilioRestClient(sid, auth_token)
    message = client.sms.messages.create(
        to=to, from_=number, body=body)
    print message
    return message


def send(to, from_, body, subject):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_
    msg["To"] = to

    smtp_server = smtplib.SMTP(
        settings["RECALL_SMTPD_HOST"],
        int(settings["RECALL_SMTPD_PORT"]))
    smtp_server.sendmail(from_, [to], msg.as_string())
    smtp_server.quit()

def invite(to, user):
    text = """Hello $name,

Follow this link to get your invite to Recall:

    https://recall.calpaterson.com/verify-email/$email_key

Reply to this email if you have any trouble!
Cal"""
    template = Template(text)
    try:
        name = user["firstName"]
    except KeyError:
        name = user["pseudonym"]
    body = template.substitute(name=name,
                               email_key=user["email_key"])
    send(to, "cal@calpaterson.com", body, "Recall Invite")
