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
from urlparse import urlparse
from robotparser import RobotFileParser
import time

import requests
from bs4 import BeautifulSoup

import convenience

settings = convenience.settings

logger = None

user_agent = "Recall - email cal@calpaterson.com for support"

def may_fetch(hyperlink):
    url_obj = urlparse(hyperlink)
    # workaround for issue with wikipedia
    if "wikipedia" in url_obj.netloc:
        return True
    robots_url = url_obj.scheme + "://" + url_obj.netloc + "/robots.txt"
    robots_parser = RobotFileParser(robots_url)
    robots_parser.read()
    allowed = robots_parser.can_fetch(user_agent, hyperlink)
    if not allowed:
        logger.warn("Not allowed to fetch " + hyperlink)
    return allowed


def get_fulltext(mark):
    headers = {"User-Agent": user_agent}
    if "hyperlink" in mark and may_fetch(mark["hyperlink"]):
        response = requests.get(mark["hyperlink"], headers=headers)
        if response.status_code in xrange(200, 300):
            mark[u"£fulltext"] = BeautifulSoup(response.content).get_text()
        logger.info("Requested {hyperlink}, got {status_code}".format(
                hyperlink=mark["hyperlink"],
                status_code=response.status_code))


def update_last_indexed_time(mark):
    mark[u"£last_indexed"] = int(time.time() * 1000)
    db = convenience.db()
    db.marks.update(
        {"@": mark["@"], "~": mark["~"]},
        {"$set": {"£last_indexed": mark[u"£last_indexed"]},
         "$unset": "£q"})


def mark_for_record(record):
    if ":" not in record:
        mark = record
    else:
        db = convenience.db()
        mark = db.marks.find_one(
            {"@": record[":"]["@"], "~": record[":"]["~"]})
        del mark["_id"]
    return mark


def index(record):
    mark = mark_for_record(record)
    update_last_indexed_time(mark)

    db = convenience.db()
    facts = db.marks.find({":": {"@": mark["@"], "~": mark["~"]}})
    for fact in facts:
        mark.setdefault("about", []).append(fact["about"])

    get_fulltext(mark)

    url = "http://{hostname}:{port}/{index}/{type}/{id}".format(
        hostname = settings["RECALL_ELASTICSEARCH_HOST"],
        port = int(settings["RECALL_ELASTICSEARCH_PORT"]),
        index = settings["RECALL_ELASTICSEARCH_INDEX"],
        type = "mark",
        id = mark["@"] + str(mark["~"]))
    requests.post(url, data=json.dumps(mark))
    logger.info("Indexed: {who}/{when}".format(who=mark["@"], when=mark["~"]))


def append_stale_marks_to_queue():
    one_week_ago = 60 * 60 * 24 * 7 * 1000
    db = convenience.db()

    stale_roots = list(db.marks.find({
                "$or": [
                    {"£last_indexed": {"$exists": False}},
                    {"£last_indexed": {"$lt": one_week_ago}}],
                "£q": {"$exists": False},
                "£created": {"$lt": one_week_ago}}))
    if stale_roots is not None and stale_roots != []:
        logger.info("Got {n} stale root records".format(n=len(stale_roots)))
        connection = convenience.redis_connection()
        for root_record in stale_roots:
            db.marks.update({"_id": root_record["_id"]},
                            {"$set": {"£q": True}})
            del root_record["_id"]
            connection.lpush("marks", json.dumps(root_record))


def next_record():
    connection = convenience.redis_connection()
    try:
        return json.loads(connection.blpop("marks", timeout=1)[1])
    except TypeError:
        pass


def main():
    convenience.load_settings()
    global logger
    logger = convenience.logger("worker")
    logger.info("Starting with settings: {settings}".format(
            settings=settings))
    while(True):
        try:
            append_stale_marks_to_queue()
            record = next_record()
            if record is not None:
                index(record)
        except Exception:
            logger.exception("Exception while indexing")

if __name__ == "__main__":
    main()
