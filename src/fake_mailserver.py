#!/usr/bin/env python2
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

import smtpd
import asyncore

from recall import convenience as conv

settings = conv.settings

class FakeMailServer(smtpd.SMTPServer):
    def __init__(self, localaddr, remoteaddr):
        self.logger = conv.logger("fake_smtpd")
        self.logger.info("Starting on port " + str(localaddr[1]))
        smtpd.SMTPServer.__init__(self, localaddr, remoteaddr)

    def process_message(self, unused_peer, mailfrom, rcpttos, data):
        mail_file_path = settings["RECALL_MAILFILE"]
        with open(mail_file_path, "w") as mailfile:
            mailfile.write(data)
        self.logger.info("Wrote to {path}, from: {from_}, to: {to}".format(
                from_=mailfrom, to=rcpttos, path=mail_file_path))

def main():
    conv.load_settings()
    FakeMailServer(("localhost", int(settings["RECALL_SMTPD_PORT"])), None)
    asyncore.loop()

if __name__ == "__main__":
    main()
