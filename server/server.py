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

from flask import Flask, request, make_response
from pymongo import Connection
from werkzeug.routing import BaseConverter
import pymongo
import bcrypt

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

@app.route("/mark/<email>/<time>", methods=["GET", "OPTIONS"])
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

@app.route("/mark", methods=["POST"])
def add_mark():
    mark_as_dict = json.loads(request.data)
    try:
        mark_as_dict[u"url"] = "http://" + config["api-hostname"] \
            + "/mark/" \
            + mark_as_dict[u"@"] \
            + "/" + str(int(mark_as_dict[u"~"]))
    except KeyError:
        return "", 400
    db = Connection("localhost", 27017).recall.marks
    db.insert(mark_as_dict)
    del(mark_as_dict["_id"])
    return json.dumps(mark_as_dict), 201

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
            "password"
            ])
    if "email" not in user_as_dict or "password" not in user_as_dict:
        return "", 400
    salt = config["password-salt"]
    user_as_dict["email_hash"] = bcrypt.hashpw(user_as_dict["email"], salt)
    user_as_dict["password_hash"] = bcrypt.hashpw(user_as_dict["password"], salt)
    del(user_as_dict["password"])
    db = Connection("localhost", 27017).recall.users
    db.ensure_index("email", unique=True)
    db.insert(user_as_dict, safe=True)
    return "", 202

@app.route("/user/<email>", methods=["UPDATE"])
def prove_email(email):
    body = may_only_contain(json.loads(request.data), [
            "email_hash"
            ])
    db = Connection("localhost", 27017).recall.users
    spec = {"email": body["email"],
            "email_hash": body["proof"]}
    update = {"$set": {"email_verified": True}}
    success = db.find_one(spec, update, safe=True)["updatedExisting"]
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
