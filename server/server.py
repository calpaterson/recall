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

from flask import Flask, request, make_response, Response
from pymongo import Connection
from werkzeug.routing import BaseConverter
import pymongo
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
    if settings["RECALL_PASSWORD_SALT"] == "salt" and\
            not settings["IS_TEST"]:
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

@app.route("/mark/<email>/<time>", methods=["GET"])
def get_mark(email, time):
    db = get_db()
    mark = db.marks.find_one({"@": email, "~": int(time)})
    try:
        del(mark[u"_id"])
    except TypeError:
        return "", 404
    return json.dumps(mark)

@app.route("/mark/<email>", methods=["GET"])
def get_all_marks_by_email(email):
    db = get_db()
    rs = db.marks.find({"@": email}, sort=[("~", pymongo.DESCENDING)])
    marks = []
    for mark in rs:
        del(mark[u"_id"])
        marks.append(mark)
    return json.dumps(marks)

@app.route("/mark", methods=["GET"])
def get_all_marks():
    db = get_db()
    rs = db.marks.find(sort=[("~", pymongo.DESCENDING)])
    marks = []
    for mark in rs:
        del(mark[u"_id"])
        marks.append(mark)
    return json.dumps(marks)

def is_authorised(body):
    db = Connection("localhost", 27017)
    password_hash = bcrypt.hashpw(body["%password"], settings["RECALL_PASSWORD_SALT"])
    user = db.recall.users.find_one(
        {"email": body["@"],
         "password_hash": password_hash})
    if user is None:
        return False
    else:
        return True

@app.route("/mark", methods=["POST"])
def add_mark():
    body = json.loads(request.data)
    if not is_authorised(body):
        return "", 403
    try:
        body[u"url"] = "http://" + settings["RECALL_API_HOSTNAME"] \
            + "/mark/" \
            + body[u"@"] \
            + "/" + str(int(body[u"~"]))
    except KeyError:
        return "", 400
    db = Connection("localhost", 27017)
    db.recall.marks.insert(body)
    del(body["_id"])
    return json.dumps(body), 201

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
    user_as_dict = may_only_contain(json.loads(request.data), [
            "pseudonym",
            "firstName",
            "surname",
            "email",
            ])
    if "email" not in user_as_dict:
        return "", 400
    user_as_dict["email_key"] = str(uuid.uuid4())
    db = get_db().users
    db.ensure_index("email", unique=True)
    db.insert(user_as_dict, safe=True)
    return "", 202

@app.route("/user/<email_key>", methods=["POST"])
def verify_email(email_key):
    body = may_only_contain(json.loads(request.data), [
            "password",
            ])
    password_hash = bcrypt.hashpw(
        body["password"],
        settings["RECALL_PASSWORD_SALT"])
    del body["password"]

    spec = {"email_key": email_key}
    update = {"$set": {"email_verified": True,
                       "password_hash": password_hash}}
    db = get_db()
    success = db.users.update(
        spec, update, safe=True)["updatedExisting"]
    if success:
        return "", 201
    else:
        return "", 400

if __name__ == "__main__":
    load_settings()
    app.run()
