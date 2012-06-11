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

from sys import argv
import json
import os
import time
import uuid

from flask import Flask, request, make_response, Response
from pymongo import Connection, DESCENDING, ASCENDING
from redis import Redis
import bcrypt
from gevent import monkey
from gevent.wsgi import WSGIServer

settings = {}

app = Flask(__name__)

class HTTPException(Exception):
    def __init__(self, message, status_code, machine_readable=None):
        self.message = message
        self.status_code = status_code
        self.machine_readable = machine_readable

def handle_exception(exception):
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

def load_settings():
    settings.update({"RECALL_MONGODB_DB_NAME": "recall",
                     "RECALL_MONGODB_HOST": "localhost",
                     "REALLL_MONGODB_PORT": "27017",
                     "RECALL_API_BASE_URL": "https://localhost:5000",
                     "RECALL_MARK_LIMIT": "100",
                     "RECALL_SERVER_PORT": "5000"})
    for name in os.environ:
        if name.startswith("RECALL_"):
            settings[name] = os.environ[name]

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

def is_authorised(require_attempt=False):
    email = request.headers.get("X-Email", None)
    password = request.headers.get("X-Password", None)
    if email is None or password is None:
        if require_attempt:
            raise HTTPException("You must include authentication headers", 400)
        return False
    user = db().users.find_one(
        {"email": email, "password_hash": {"$exists": True}})
    if user is None:
        return False
    if user["password_hash"] != bcrypt.hashpw(password, user["password_hash"]):
        return False
    return user

def make_mark_url(mark):
    return settings["RECALL_API_BASE_URL"] + "/mark/" \
        + mark[u"@"] + "/" + str(int(mark["~"]))

@app.route("/mark", methods=["POST"])
def add_mark():
    def insert_mark(body):
        assert "~" in body and "@" in body, "Must include @ and ~ with all marks"
        has_no_problematic_keys(body)
        body[u"£created"] = unixtime()
        db().marks.insert(body)
        del body["_id"]
        redis_connection().lpush("marks", json.dumps(body))
        return body

    if not is_authorised(require_attempt=True):
        raise HTTPException("Email or password or both do not match", 403)
    body = json.loads(request.data)
    try:
        if type(body) == list:
            for mark in body:
                insert_mark(mark)
            return "null", 202
        elif type(body) == dict:
            body = insert_mark(body)
            return json.dumps(body), 201
    except KeyError:
        return "You must include at least @ and ~", 400

@app.route("/mark", methods=["GET"])
def get_all_marks():
    maximum = int(request.args.get("maximum", 0))
    since = int(request.args.get("since", 0))
    before = int(request.args.get("before", 0))
    spec = {"%private": {"$exists": False}}
    if since != 0:
        spec["~"] = {"$gt": since}
    if before != 0:
        spec["~"] = {"$lt": before}
    try:
        user = is_authorised()
        if user:
            spec = {"$or": [
                    {"@": user["email"]},
                    {"%private": {"$exists": False}},
                    ],
                    }
            if since != 0:
                spec["~"] = {"$gt": since}
            if before != 0:
                spec["~"] = {"$lt": before}
    except KeyError:
        pass
    rs = db().marks.find(spec, sort=[("~", DESCENDING)], limit=maximum)
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

@app.route("/mark/<email>", methods=["GET"])
def get_all_marks_by_email(email):
    maximum = int(request.args.get("maximum", 0))
    since = int(request.args.get("since", 0))
    before = int(request.args.get("before", 0))
    spec = {"%private": {"$exists": False},
            "@": email}
    if since != 0:
        spec["~"] = {"$gt": since}
    if before != 0:
        spec["~"] = {"$lt": before}
    try:
        user = is_authorised()
        if user:
            spec = {"$or": [
                    {"@": user["email"]},
                    {"%private": {"$exists": False}}]}
            if since != 0:
                spec["~"] = {"$gt": since}
            if before != 0:
                spec["~"] = {"$lt": before}
    except KeyError:
        pass
    rs = db().marks.find(spec, sort=[("~", DESCENDING)], limit=maximum)
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

@app.route("/mark/<email>/<time>", methods=["GET"])
def get_mark(email, time):
    spec = {"%private": {"$exists": False},
            "@": email,
            "~": int(time)}
    try:
        user = is_authorised()
        if user:
            spec = {"$or": [
                    {"@": user["email"]},
                    {"%private": {"$exists" : False}}
                    ],
                    "~": int(time)}
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
    if is_authorised() == user:
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
    if "RECALL_TEST_MODE" in settings:
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
    load_settings()
    if "RECALL_DEBUG_MODE" not in settings:
        monkey.patch_socket()

    http_server = WSGIServer(('', int(settings["RECALL_API_PORT"])), app)
    http_server.serve_forever()
