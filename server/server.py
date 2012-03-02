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

from flask import Flask, request
from pymongo import Connection

config = {}

app = Flask(__name__)

@app.route("/mark/<email>/<time>", methods=["GET"])
def getMark(email, time):
    db = Connection("localhost", 27017).recall.marks
    mark = db.find_one({"email": email, "time": int(time)})
    del(mark[u"_id"])
    return json.dumps(mark)

@app.route("/mark/<email>", methods=["GET"])
def getAllMarks(email):
    db = Connection("localhost", 27017).recall.marks
    rs = db.find({"email": email})
    marks = []
    for mark in rs:
        del(mark[u"_id"])
        marks.append(mark)
    return json.dumps(marks)

@app.route("/mark", methods=["POST"])
def addMark():
    mark_as_dict = json.loads(request.json)
    mark_as_dict[u"url"] = config["api-hostname"] + "/mark/" + mark_as_dict[u"email"] \
        + "/" + str(mark_as_dict[u"time"])
    db = Connection("localhost", 27017).recall.marks
    db.insert(mark_as_dict)
    del(mark_as_dict["_id"])
    return json.dumps(mark_as_dict), 201

if __name__ == "__main__":
    config = json.loads(open(argv[1]).read())
    app.run()
