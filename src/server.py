#! /usr/bin/env python
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


from wsgiref.simple_server import make_server
import signal

import bottle

from recall import (
    people,
    bookmarks,
    convenience,
    status,
    )

settings = convenience.settings

logger = None

def stop(unused_signal, unused_frame):
    logger.info("Stopping")
    exit(0)

def main():
    try:
        global logger
        convenience.load_settings()
        logger = convenience.logger("server")
        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)
        logger.info("Starting")
        app = bottle.Bottle()
        app.mount("/people", people.app)
        app.mount("/bookmarks", bookmarks.app)
        app.mount("/status", status.app)
        http_server = make_server("", int(settings["RECALL_API_PORT"]), app)
        http_server.serve_forever()
    except KeyboardInterrupt:
        stop(None, None)

if __name__ == "__main__":
    main()
