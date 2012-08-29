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
import traceback

import requests
from bs4 import BeautifulSoup

import convenience

settings = convenience.settings

def index(record):
    def is_root(record):
        return ":" not in record
    def get_fulltext(mark):
        if "hyperlink" in mark:
            response = requests.get(mark["hyperlink"])
            if response.status_code in xrange(200, 300):
                mark["£fulltext"] = BeautifulSoup(response.content).get_text()
            else:
                print "Unable to download"

    db = convenience.db()

    if is_root(record):
        mark = record
    else:
        mark = db.marks.find_one(
            {"@": record[":"]["@"], "~": record[":"]["~"]})

    if "_id" in mark:
        del mark["_id"]

    facts = db.marks.find({":": {"@": mark["@"], "~": mark["~"]}})
    for fact in facts:
        mark.setdefault("about", []).append(fact["about"])

    get_fulltext(mark)

    print "Reindexing: {mark}".format(mark=mark)

    url = "http://{hostname}:{port}/{index}/{type}/{id}".format(
        hostname = settings["RECALL_ELASTICSEARCH_HOST"],
        port = int(settings["RECALL_ELASTICSEARCH_PORT"]),
        index = settings["RECALL_ELASTICSEARCH_INDEX"],
        type = "mark",
        id = mark["@"] + str(mark["~"]))
    requests.post(url, data=json.dumps(mark))


def index_new_mark():
    def pop_mark():
        connection = convenience.redis_connection()
        entry = connection.blpop("marks")
        mark_as_string = entry[1]
        return json.loads(mark_as_string)

    mark = pop_mark()
    index(mark)

def main():
    convenience.load_settings()
    while(True):
        try:
            index_new_mark()
        except Exception as e:
            traceback.print_exc(e)

if __name__ == "__main__":
    main()
