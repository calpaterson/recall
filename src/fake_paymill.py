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

import signal
import os
from wsgiref.simple_server import make_server

from bottle import Bottle

from recall import plugins

app = Bottle()

settings = {}

transaction_identifier = "t1"
payment_identifier = "p1"
subscription_identifier = "s1"
client_identifier = "c1"

def check_authentication():
    pass

@app.get("/transactions")
def get_transactions():
    return {"data": [{"client": {"id": client_identifier}, "status": "closed"}]}

@app.post("/clients")
def post_clients():
    return {"data": {"id": client_identifier}}

@app.post("/subscriptions")
def post_subscriptions():
    return {"data": {"id": subscription_identifier}}

@app.post("/payments")
def post_payments():
    return {"data": {"id": payment_identifier}}

def stop(unused_signal, unused_frame):
    exit(0)

def main():
    try:
        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)
        for name in os.environ:
            if name.startswith("RECALL_"):
                settings[name] = os.environ[name]
        app.install(plugins.ppjson)
        http_server = make_server("", 6565, app)
        http_server.serve_forever()
    except KeyboardInterrupt:
        stop(None, None)

if __name__ == '__main__':
    main()
