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
from sys import argv
import os
import time

from flask import Flask, request, make_response, Response
from pymongo import Connection, DESCENDING
from werkzeug.routing import BaseConverter
import bcrypt
import uuid

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

    if not isinstance(exception, HTTPException):
        return json_error("Unknown exception: " + exception.message), 500
    else:
        return json_error(exception.message), exception.status_code

app.handle_exception = handle_exception

def load_settings():
    settings["RECALL_MONGODB_DB_NAME"] = os.environ.get(
        "RECALL_MONGODB_DB_NAME", "recall")
    settings["RECALL_MONGODB_HOST"] = os.environ.get(
        "RECALL_MONGODB_HOST", "localhost")
    settings["RECALL_MONGODB_PORT"] = os.environ.get(
        "RECALL_MONGODB_PORT", 27017)
    settings["RECALL_PASSWORD_SALT"] = os.environ.get(
        "RECALL_PASSWORD_SALT", "$2a$12$tl2VDOPWJOuoJsnu6xQtWu")
    settings["RECALL_API_BASE_URL"] = os.environ.get(
        "RECALL_API_HOSTNAME", "https://localhost:5000")
    settings["RECALL_MARK_LIMIT"] = os.environ.get("RECALL_MARK_LIMIT", 100)
    if os.environ.get("RECALL_DEBUG_MODE") == "false":
        settings["RECALL_DEBUG_MODE"] = False
    else:
        settings["RECALL_DEBUG_MODE"] = True

def get_db():
    db_name = settings["RECALL_MONGODB_DB_NAME"]
    return Connection(
        settings["RECALL_MONGODB_HOST"],
        settings["RECALL_MONGODB_PORT"])[db_name]

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

def may_only_contain(dict_, whitelist):
    d = {}
    for k, v in dict_.items():
        if k in whitelist:
            d[k] = v
    return d

def json_error(message):
    return json.dumps({"error": message})

def get_unixtime():
    if app.testing:
        return 0
    else:
        return int(time.time())

def is_authorised(require_attempt=False):
    db = get_db()
    email = request.headers.get("X-Email", None)
    password = request.headers.get("X-Password", None)
    if email is None or password is None:
        if require_attempt:
            raise HTTPException("You must include authentication headers", 400)
        return False
    password_hash = bcrypt.hashpw(
        password,
        settings["RECALL_PASSWORD_SALT"])
    user = db.users.find_one(
        {"email": email,
         "password_hash": password_hash})
    if user is None:
        return False
    else:
        return user

def make_mark_url(time):
    return settings["RECALL_API_BASE_URL"] + "/mark/" \
        + body[u"@"] + "/" + str(int(body[u"~"]))

@app.route("/mark", methods=["POST"])

def add_mark():
    def make_url(body):
        return settings["RECALL_API_BASE_URL"] + "/mark/" \
            + body[u"@"] + "/" + str(int(body[u"~"]))
    def insert_mark(body):
        has_no_problematic_keys(body)
        body[u"%url"] = make_url(body)
        body[u"£created"] = get_unixtime()
        db = get_db()
        db.marks.insert(body)
        del body["_id"]
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
    db = get_db()
    rs = db.marks.find(spec, sort=[("~", DESCENDING)], limit=maximum)
    marks = []
    counter = 0
    for mark in rs:
        del(mark[u"_id"])
        marks.append(mark)
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
    db = get_db()
    rs = db.marks.find(spec, sort=[("~", DESCENDING)], limit=maximum)
    marks = []
    counter = 0
    for mark in rs:
        del(mark[u"_id"])
        marks.append(mark)
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
    db = get_db()
    mark = db.marks.find_one(spec)
    try:
        del(mark[u"_id"])
    except TypeError:
        return json_error("No such mark found"), 404
    return json.dumps(mark), 200

@app.route("/user/<email>", methods=["GET"])
def user(email):
    users = get_db().users
    user = users.find_one({"email": email})
    if user is None:
        return "", 404

    return_value = may_only_contain(user, [
            "pseudonym",
            "firstName",
            "surname",
            "email"])
    if is_authorised() == user:
        return_value["self"] = True
    return json.dumps(return_value), 200

@app.route("/user", methods=["POST"])
def request_invite():
    body = may_only_contain(json.loads(request.data), [
            "pseudonym",
            "firstName",
            "surname",
            "email",
            ])
    if "email" not in body:
        return "You must provide an email field", 400
    body["email_key"] = str(uuid.uuid4())
    body["registered"] = get_unixtime()
    db = get_db().users
    db.ensure_index("email", unique=True)
    db.insert(body, safe=True)
    return "", 202

@app.route("/user/<email_key>", methods=["POST"])
def verify_email(email_key):
    body = may_only_contain(json.loads(request.data), [
            "%password",
            ])
    password_hash = bcrypt.hashpw(
        body["%password"],
        settings["RECALL_PASSWORD_SALT"])
    del body["%password"]

    spec = {"email_key": email_key}
    update = {"$set": {"email_verified": get_unixtime(),
                       "password_hash": password_hash}}
    db = get_db()
    success = db.users.update(
        spec, update, safe=True)["updatedExisting"]
    user = db.users.find_one({"email_key": email_key})
    del user["password_hash"]
    del user["email_key"]
    del user["_id"]
    if success:
        return json.dumps(user), 201
    else:
        return "No such verification key found", 400

if __name__ == "__main__":
    load_settings()
    app.run(debug=settings["RECALL_DEBUG_MODE"])
