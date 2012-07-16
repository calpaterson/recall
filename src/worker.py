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

import requests

import convenience

settings = convenience.settings

def index_root(root):
    url = "http://{hostname}:{port}/{index_root}/{type}/{id}".format(
        hostname = settings["RECALL_ELASTICSEARCH_HOST"],
        port = int(settings["RECALL_ELASTICSEARCH_PORT"]),
        index_root = settings["RECALL_ELASTICSEARCH_INDEX"],
        type = "mark",
        id = root["@"] + str(root["~"]))
    db = convenience.db()
    facts = db.marks.find({":": {"@": root["@"], "~": root["~"]}})
    for fact in facts:
        root.setdefault("about", []).append(fact["about"])
    requests.post(url, data=json.dumps(root))

def index_fact(fact):
    db = convenience.db()
    root = db.marks.find_one({"@": fact[":"]["@"], "~": fact[":"]["~"]})
    try:
        root.setdefault("about", []).append(fact["about"])
        del root["_id"]
        url = "http://{hostname}:{port}/{index_root}/{type}/{id}".format(
            hostname = settings["RECALL_ELASTICSEARCH_HOST"],
            port = int(settings["RECALL_ELASTICSEARCH_PORT"]),
            index_root = settings["RECALL_ELASTICSEARCH_INDEX"],
            type = "mark",
            id = root["@"] + str(root["~"]))
        requests.post(url, data=json.dumps(root))
    except:
        pass

def index_new_marks():
    def pop_mark():
        connection = convenience.redis_connection()
        entry = connection.blpop("marks")
        mark_as_string = entry[1]
        return json.loads(mark_as_string)

    def is_root(mark):
        return ":" not in mark

    mark = pop_mark()
    if is_root(mark):
        index_root(mark)
    else:
        index_fact(mark)

def main():
    pass

if __name__ == "__main__":
    convenience.load_settings()
    while(True):
        index_new_marks()
