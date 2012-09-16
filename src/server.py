#! /usr/bin/env python
from wsgiref.simple_server import make_server

import bottle

import people
import bookmarks
import convenience

settings = convenience.settings

if __name__ == "__main__":
    convenience.load_settings()
    app = bottle.Bottle()
    app.mount("/people", people.app)
    app.mount("/bookmarks", bookmarks.app)
    http_server = make_server("", int(settings["RECALL_API_PORT"]), app)
    http_server.serve_forever()
