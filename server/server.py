#!/usr/bin/env python

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

def load_settings():
    settings["RECALL_MONGODB_DB_NAME"] = os.environ.get(
        "RECALL_MONGODB_DB_NAME", "recall")
    settings["RECALL_MONGODB_HOST"] = os.environ.get(
        "RECALL_MONGODB_HOST", "localhost")
    settings["RECALL_MONGODB_PORT"] = os.environ.get(
        "RECALL_MONGODB_PORT", 27017)
    settings["RECALL_PASSWORD_SALT"] = os.environ.get(
        "RECALL_PASSWORD_SALT", "$2a$12$tl2VDOPWJOuoJsnu6xQtWu")
    settings["RECALL_API_HOSTNAME"] = os.environ.get(
        "RECALL_API_HOSTNAME", "localhost:5000")
    if os.environ.get("RECALL_DEBUG_MODE") == "false":
        settings["RECALL_DEBUG_MODE"] = False
    else:
        settings["RECALL_DEBUG_MODE"] = True
    if settings["RECALL_PASSWORD_SALT"] == "salt":
        print "ERROR: Using bogus salt"

def get_db():
    db_name = settings["RECALL_MONGODB_DB_NAME"]
    return Connection(
        settings["RECALL_MONGODB_HOST"],
        settings["RECALL_MONGODB_PORT"])[db_name]

def may_only_contain(dict_, whitelist):
    """Takes a dict and a whitelist of keys and removes all items in the dict
    not in the whitelist"""
    d = {}
    for k, v in dict_.items():
        if k in whitelist:
            d[k] = v
    return d

def json_error(message):
    return json.dumps({"error": message})

def is_authorised(email, password):
    db = get_db()
    password_hash = bcrypt.hashpw(
        password,
        settings["RECALL_PASSWORD_SALT"])
    user = db.users.find_one(
        {"email": email,
         "password_hash": password_hash})
    if user is None:
        return False
    else:
        return True

@app.route("/mark", methods=["POST"])
def add_mark():
    def make_url(body):
        return "http://" + settings["RECALL_API_HOSTNAME"] + "/mark/" \
            + body[u"@"] + "/" + str(int(body[u"~"]))
    def insert_mark(body):
        body[u"%url"] = make_url(body)
        db = get_db()
        db.marks.insert(body)
        del body["_id"]
        return body

    try:
        if not is_authorised(
            request.headers["X-Email"],
            request.headers["X-Password"]):
            return "Email or password or both does not match", 403
    except KeyError:
        return json_error("You must include authentication headers"), 400
    body = json.loads(request.data)
    try:
        if type(body) == list:
            for mark in body:
                insert_mark(mark)
            return "{}", 202
        elif type(body) == dict:
            body = insert_mark(body)
            return json.dumps(body), 201
    except KeyError:
        return "You must include at least @ and ~", 400

@app.route("/mark", methods=["GET"])
def get_all_marks():
    spec = {"%private": {"$exists": False}}
    try:
        email = request.headers["X-Email"]
        password = request.headers["X-Password"]
        if is_authorised(email, password):
            spec = {"$or": [
                    {"@": email},
                    {"%private": {"$exists": False}}
                    ]}
    except KeyError:
        pass
    db = get_db()
    rs = db.marks.find(
        spec,
        sort=[("~", DESCENDING)])
    marks = []
    for mark in rs:
        del(mark[u"_id"])
        marks.append(mark)
    return json.dumps(marks)

@app.route("/mark/<email>", methods=["GET"])
def get_all_marks_by_email(email):
    spec = {"%private": {"$exists": False},
            "@": email}
    try:
        email = request.headers["X-Email"]
        password = request.headers["X-Password"]
        if is_authorised(email, password):
            spec = {"$or": [
                    {"@": email},
                    {"%private": {"$exists": False}}
                    ]}
    except KeyError:
        pass
    db = get_db()
    rs = db.marks.find(spec, sort=[("~", DESCENDING)])
    marks = []
    for mark in rs:
        del(mark[u"_id"])
        marks.append(mark)
    return json.dumps(marks)

@app.route("/mark/<email>/<time>", methods=["GET"])
def get_mark(email, time):
    spec = {"%private": {"$exists": False},
            "@": email,
            "~": int(time)}
    try:
        email = request.headers["X-Email"]
        password = request.headers["X-Password"]
        if is_authorised(email, password):
            spec = {"$or": [
                    {"@": email},
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
    user = users.find_one(email)
    if user is None:
        return "", 404
    else:
        return may_only_contain(user, [
                "pseudonym",
                "firstName",
                "surname",
                "email"])

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
    body["registered"] = int(time.time())
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
    update = {"$set": {"email_verified": int(time.time()),
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
