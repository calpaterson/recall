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

from flask import Flask, request, make_response, Response
from pymongo import Connection
from werkzeug.routing import BaseConverter
import pymongo
import bcrypt
import uuid

config = None

app = Flask(__name__)

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
    db = Connection("localhost", 27017).recall.marks
    mark = db.find_one({"@": email, "~": int(time)})
    try:
        del(mark[u"_id"])
    except TypeError:
        return "", 404
    return json.dumps(mark)

@app.route("/mark/<email>", methods=["GET"])
def get_all_marks_by_email(email):
    db = Connection("localhost", 27017).recall.marks
    rs = db.find({"@": email}, sort=[("~", pymongo.DESCENDING)])
    marks = []
    for mark in rs:
        del(mark[u"_id"])
        marks.append(mark)
    return json.dumps(marks)

@app.route("/mark", methods=["GET"])
def get_all_marks():
    db = Connection("localhost", 27017).recall.marks
    rs = db.find(sort=[("~", pymongo.DESCENDING)])
    marks = []
    for mark in rs:
        del(mark[u"_id"])
        marks.append(mark)
    return json.dumps(marks)

def is_authorised(body):
    db = Connection("localhost", 27017)
    password_hash = bcrypt.hashpw(body["%password"], config["password-salt"])
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
        body[u"url"] = "http://" + config["api-hostname"] \
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
    users = Connection("localhost", 27017).recall.users
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
    db = Connection("localhost", 27017).recall.users
    db.ensure_index("email", unique=True)
    db.insert(user_as_dict, safe=True)
    return "", 202

@app.route("/user/<email>", methods=["POST"])
def verify_email(email):
    body = may_only_contain(json.loads(request.data), [
            "password",
            "email_key"
            ])
    password_hash = bcrypt.hashpw(body["password"], config["password-salt"])
    del body["password"]
    db = Connection("localhost", 27017).recall.users
    spec = {"email": email,
            "email_key": body["email_key"]}
    update = {"$set": {"email_verified": True,
                       "password_hash": password_hash}}
    success = db.update(spec, update, safe=True)["updatedExisting"]
    if success:
        return "", 201
    else:
        return "", 400

if __name__ == "__main__":
    try:
        config = json.loads(open(argv[1]).read())
    except IndexError:
        print "ERROR: Need configuration file"
        exit(1)
    app.run(debug=True)
