#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

import json
import os
import sys
import time
import traceback
import uuid

from flask import Flask, request, make_response, Response, g
from pymongo import Connection, DESCENDING, ASCENDING
from redis import Redis
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.wsgi import WSGIContainer
import bcrypt
import requests

import convenience

app = Flask(__name__)

settings = convenience.settings

class HTTPException(Exception):
    def __init__(self, message, status_code, machine_readable=None):
        self.message = message
        self.status_code = status_code
        self.machine_readable = machine_readable

def handle_exception(exception):
    print >> sys.stderr, traceback.format_exc(),
    def json_error(message):
        document = {"human_readable": message}
        if hasattr(exception, "machine_readable") and \
                exception.machine_readable is not None:
            document["machine_readable"] = exception.machine_readable
        return json.dumps(document)

    if isinstance(exception, HTTPException):
        return json_error(exception.message), exception.status_code
    if isinstance(exception, AssertionError):
        return json_error(exception.message), 400
    else:
        return json_error("Unknown exception: " + exception.message), 500

app.handle_exception = handle_exception

def db():
    db_name = settings["RECALL_MONGODB_DB_NAME"]
    return Connection(
        settings["RECALL_MONGODB_HOST"],
        int(settings["RECALL_MONGODB_PORT"]))[db_name]

def redis_connection():
    return Redis(
        host=settings["RECALL_REDIS_HOST"],
        port=int(settings["RECALL_REDIS_PORT"]),
        db=int(settings["RECALL_REDIS_DB"]))

def has_no_problematic_keys(mark):
    mark_queue = []
    current = mark
    while True:
        for key in current:
            if key.startswith("$") or key.startswith(u"£"):
                raise HTTPException(
                    "Mark keys may not be prefixed with $ or £", 400,
                    machine_readable=key)
            if isinstance(current[key], dict):
                mark_queue.insert(0, current[key])
        if mark_queue == []:
            return
        else:
            current = mark_queue.pop()

def whitelist(dict_, whitelist):
    d = {}
    for k, v in dict_.items():
        if k in whitelist:
            d[k] = v
    return d

def blacklist(dict_, blacklist):
    d = {}
    for k, v in dict_.items():
        if k not in blacklist:
            d[k] = v
    return d

def json_error(message):
    return json.dumps({"error": message})

def unixtime():
    if app.testing:
        return 0
    else:
        return int(time.time())

@app.before_request
def authentication():
    try:
        email = request.headers["X-Email"]
        password = request.headers["X-Password"]
        g.user = db().users.find_one(
            {"email": email, "password_hash": {"$exists": True}})
        assert g.user["password_hash"] == bcrypt.hashpw(
            password, g.user["password_hash"])
    except (KeyError, TypeError):
        g.user = None
    except AssertionError:
        raise HTTPException("Email or password or both do not match", 403)

def require_authentication(f):
    def decorated(*args, **kwargs):
        if g.user is None:
            raise HTTPException("You must include authentication headers", 400)
        return f(*args, **kwargs)
    return decorated

def make_mark_url(mark):
    return settings["RECALL_API_BASE_URL"] + "/mark/" \
        + mark[u"@"] + "/" + str(int(mark["~"]))

@app.route("/mark", methods=["POST"])
@require_authentication
def add_marks():
    def insert_mark(body):
        assert "~" in body and "@" in body, "Must include @ and ~ with all marks"
        has_no_problematic_keys(body)
        body[u"£created"] = unixtime()
        db().marks.insert(body)
        del body["_id"]
        redis_connection().lpush("marks", json.dumps(body))
        return body

    marks = json.loads(request.data)

    if type(marks) == dict:
        marks = [marks]
    try:
        for mark in marks:
            assert "@" in mark
            assert "~" in mark
    except AssertionError:
        raise HTTPException("Must include @ and ~ with all marks", 400)

    for mark in marks:
        insert_mark(mark)
    return "null", 202

@app.route("/mark", methods=["GET"])
def get_all_marks():
    if "q" in request.args:
        return search(request.args["q"])
    else:
        return marks()

@app.route("/mark/<email>", methods=["GET"])
def get_all_marks_by_email(email):
    spec_additions = {"@": email}
    return marks(spec_additions)

@convenience.on_json
def results_to_marks(body):
    marks = []
    for mark in body["hits"]["hits"]:
        marks.append(mark["_source"])
    return marks

def search(query_string):
    def inner_query_builder():
        return {"text":{"_all": query_string}}
    def filter_builder():
        privacy_clause = {"not": {"term":{"%private":True}}}
        if g.user is not None:
            who = g.user["email"].split("@")[0] # FIXME
            return {"or": [ privacy_clause, {"term":{"@":who}}]}
        else:
            return privacy_clause
    query = json.dumps(
        {
            "size": 100,
            "query": {
                "filtered":{
                    "query" : inner_query_builder(),
                    "filter": filter_builder()
                    }
                }
            }
        )
    url = convenience.get_es_mark_url() +  "/_search?"
    r = requests.get(url, data=query)
    return results_to_marks(r.content)

def marks(spec_additions={}):
    spec = _build_spec(spec_additions)
    limit = int(request.args.get("maximum", 0))
    rs = db().marks.find(spec, sort=[("~", DESCENDING)],
                         limit=limit)
    marks = []
    counter = 0
    for mark in rs:
        del(mark[u"_id"])
        marks.append(mark)
        mark[u"%url"] = make_mark_url(mark)
        counter += 1
        if counter > settings["RECALL_MARK_LIMIT"]:
            raise HTTPException(
                "May not request more than %s marks at once"
                % settings["RECALL_MARK_LIMIT"],
                413, machine_readable=settings["RECALL_MARK_LIMIT"])
    return json.dumps(marks)

def _build_spec(spec_additions):
    spec = {}
    _respect_privacy(spec)

    if int(request.args.get("since", 0)) != 0:
        spec["~"] = {"$gt": int(request.args.get("since", 0))}
    if int(request.args.get("before", 0)) != 0:
        spec["~"] = {"$lt": int(request.args.get("before", 0))}
    spec.update(spec_additions)
    return spec

def _respect_privacy(spec):
    if g.user:
        spec.update({"$or": [
                {"@": g.user["email"]},
                {"%private": {"$exists": False}}]})
    else:
        spec.update({"%private": {"$exists": False}})

@app.route("/mark/<email>/<time>", methods=["GET"])
def get_mark(email, time):
    spec = {"%private": {"$exists": False},
            "@": email,
            "~": int(time)}
    try:
        if g.user:
            spec = {"$or": [
                    {"@": g.user["email"]},
                    {"%private": {"$exists" : False}}
                    ]}
            spec.update({"~": int(time)})
    except KeyError:
        pass
    mark = db().marks.find_one(spec)
    try:
        del(mark[u"_id"])
        mark[u"%url"] = make_mark_url(mark)
    except TypeError:
        return json_error("No such mark found"), 404
    return json.dumps(mark), 200

@app.route("/user/<email>", methods=["GET"])
def user(email):
    users = db().users
    user = users.find_one({"email": email})
    if user is None:
        return "null", 404

    return_value = whitelist(user, [
            "pseudonym",
            "firstName",
            "surname",
            "email"])
    if g.user == user:
        return_value["self"] = True
    return json.dumps(return_value), 200

@app.route("/user", methods=["POST"])
def request_invite():
    body = whitelist(json.loads(request.data), [
            "pseudonym",
            "firstName",
            "surname",
            "email",
            ])
    if "email" not in body:
        return "You must provide an email field", 400
    body["email_key"] = str(uuid.uuid4())
    body["registered"] = unixtime()
    db().users.ensure_index("email", unique=True)
    db().users.insert(body, safe=True)
    return "null", 202

@app.route("/user/<email_key>", methods=["POST"])
def verify_email(email_key):
    if "RECALL_TEST_MODE" in settings or "RECALL_DEBUG_MODE" in settings:
        salt = bcrypt.gensalt(1)
    else:
        salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(json.loads(request.data)["password"], salt)

    spec = {"email_key": email_key, "email": json.loads(request.data)["email"],
            "verified": {"$exists": False}}
    update = {"$set": {"password_hash": password_hash,
                       "verified": unixtime()}}
    success = db().users.update(spec, update, safe=True)["updatedExisting"]
    if not success:
        if db().users.find_one({"email_key": email_key, "email": json.loads(request.data)["email"]}):
            raise HTTPException("Already verified", 403)
        else:
            raise HTTPException("No such email_key or wrong email", 404)
    user = db().users.find_one({"email_key": email_key})
    return json.dumps(blacklist(
            user, ["_id", "email_key", "password_hash"])), 201

@app.route("/linked/<who>/<when>", methods=["GET"])
def linked(who, when):
    spec = {"$or": [
            {"%private": {"$exists": False},
             "@": who,
             "~": int(when)},
            {"%private": {"$exists": False},
             u":.@": who,
             u":.~": int(when)
             }
            ]}
    found = []
    for mark in db().marks.find(spec).sort(":", ASCENDING):
        del(mark[u"_id"])
        mark[u"%url"] = make_mark_url(mark)
        found.append(mark)
    return json.dumps(list(found))

if __name__ == "__main__":
    convenience.load_settings()

    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(int(settings["RECALL_API_PORT"]))
    IOLoop.instance().start()
