#!/usr/bin/env python

import smtpd
import asyncore

import convenience as conv

settings = conv.settings

class FakeMailServer(smtpd.SMTPServer):
    def __init__(self, localaddr, remoteaddr):
        self.logger = conv.logger("fake_smtpd")
        self.logger.info("Starting on port " + str(localaddr[1]))
        smtpd.SMTPServer.__init__(self, localaddr, remoteaddr)

    def process_message(self, peer, mailfrom, rcpttos, data):
        self.logger.info("Message recieved, from: {from_}, to: {to}".format(
                from_=mailfrom, to=rcpttos))
        mail_file_path = settings["RECALL_MAILFILE"]
        with open(mail_file_path, "w") as mailfile:
            mailfile.write(data)
        self.logger.info("Wrote to " + mail_file_path)

def main():
    conv.load_settings()
    smtpserver = FakeMailServer(
        ("localhost", int(settings["RECALL_SMTPD_PORT"])), None)
    asyncore.loop()

if __name__ == "__main__":
    main()
