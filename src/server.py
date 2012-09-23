#! /usr/bin/env python
from wsgiref.simple_server import make_server
import signal

import bottle

import people
import bookmarks
import convenience

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
        logger.info("Starting with settings: {settings}".format(
                settings=settings))
        app = bottle.Bottle()
        app.mount("/people", people.app)
        app.mount("/bookmarks", bookmarks.app)
        http_server = make_server("", int(settings["RECALL_API_PORT"]), app)
        http_server.serve_forever()
    except KeyboardInterrupt:
        stop(None, None)

if __name__ == "__main__":
    main()
