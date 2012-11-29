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

from recall.convenience import settings
from recall import convenience as conv
from recall import jobs

_invite_template = """Hello $name,

Follow this link to get your invite to Recall:

    $base_url/people/verify-email/$email_key

Reply to this email if you have any trouble!
Cal"""

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

class SendInvite(jobs.Job):
    def __init__(self, user):
        self.user = user

    def _name(self):
        try:
            name = self.user["firstName"]
            return name + " " + self.user["surname"]
        except KeyError:
            return self.user["pseudonym"]

    def do(self):
        logger = conv.logger("SendInvite")
        template = Template(_invite_template)
        body = template.substitute(
            base_url=conv.settings["RECALL_API_BASE_URL"],
            name=self._name(),
            email_key=self.user["email_key"])
        email_(self.user["private_email"], "cal@calpaterson.com", body,
                        "Recall Invite")
        logger.info("Sent invite email to " + self.user["email"])
