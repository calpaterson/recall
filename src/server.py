#! /usr/bin/env python
from wsgiref.simple_server import make_server
import signal

import bottle

import people
import bookmarks
import convenience
import supervision

settings = convenience.settings

def main():
    try:
        global logger
        convenience.load_settings()
        logger = convenience.logger("server")
        supervision.as_subprocess(logger)
        logger.info("Starting with settings: {settings}".format(
                settings=settings))
        app = bottle.Bottle()
        app.mount("/people", people.app)
        app.mount("/bookmarks", bookmarks.app)
        http_server = make_server("", int(settings["RECALL_API_PORT"]), app)
        http_server.serve_forever()
    except KeyboardInterrupt:
        shutdown()

if __name__ == "__main__":
    main()
