# Recall is a program for storing bookmarks of different things
# Copyright (C) 2012  Cal Paterson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import smtplib
from email.mime.text import MIMEText
from string import Template

# from twilio.rest import TwilioRestClient

from recall. convenience import settings

def text(to, body):
    pass
    # sid = settings["RECALL_TWILIO_SID"]
    # auth_token = settings["RECALL_TWILIO_AUTH_TOKEN"]
    # number = settings["RECALL_TWILIO_PHONE_NUMBER"]
    # client = TwilioRestClient(sid, auth_token)
    # message = client.sms.messages.create(
    #     to=to, from_=number, body=body)

def email_(to, from_, body, subject):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_
    msg["To"] = to

    smtp_server = smtplib.SMTP(
        settings["RECALL_SMTPD_HOST"],
        int(settings["RECALL_SMTPD_PORT"]))
    smtp_server.sendmail(from_, [to], msg.as_string())
    smtp_server.quit()
