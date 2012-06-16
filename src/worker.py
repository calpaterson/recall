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

import os
import logging
import json
import time

import requests
from redis import Redis

_settings = {}

def load_settings():
    for name in os.environ:
        if name.startswith("RECALL_"):
            _settings[name] = os.environ[name]

def index_new_marks():
    def index(name, value):
        url = "http://{hostname}:{port}/{index}/{type}/{id}".format(
            hostname = _settings["RECALL_ELASTICSEARCH_HOST"],
            port = int(_settings["RECALL_ELASTICSEARCH_PORT"]),
            index = _settings["RECALL_ELASTICSEARCH_INDEX"],
            type = "mark",
            id = name)
        requests.post(url, data=json.dumps(value))

    def redis_connection():
        return Redis(
            host=_settings["RECALL_REDIS_HOST"],
            port=int(_settings["RECALL_REDIS_PORT"]),
            db=int(_settings["RECALL_REDIS_DB"]))

    def pop_mark():
        connection = redis_connection()
        entry = connection.blpop("marks")
        mark_as_string = entry[1]
        return json.loads(mark_as_string)

    def is_root(mark):
        return ":" not in mark

    def build_from_links(mark):
        url = "http://{hostname}:{port}/linked/{email}/{unixtime}".format(
            hostname = _settings["RECALL_API_HOST"],
            port = _settings["RECALL_API_PORT"],
            email = mark["@"],
            unixtime = mark["~"])
        print url
        linked_marks = json.loads(requests.get(url))
        for mark in linked_marks:
            print marks
            if is_root(mark):
                pass
            else:
                pass

    mark = pop_mark()
    if is_root(mark):
        index(mark["@"] + str(mark["~"]), mark)
    else:
        pass

if __name__ == "__main__":
    load_settings()
    while(True):
        index_new_marks()
