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

from urllib.parse import urlparse
import pickle
import json
import robotexclusionrulesparser as rerp
import time
from string import Template
from abc import ABCMeta, abstractmethod

import requests
from bs4 import BeautifulSoup
from redis import StrictRedis

from recall import messages
from recall import convenience as conv

def redis_connection():
    settings = conv.settings
    return StrictRedis(
        host=settings["RECALL_REDIS_HOST"],
        port=int(settings["RECALL_REDIS_PORT"]),
        db=int(settings["RECALL_REDIS_DB"]))

def enqueue(job, priority=5):
    sub_queue = "work" + str(priority)
    return redis_connection().rpush(sub_queue, pickle.dumps(job, protocol=2))

def dequeue():
    sub_queues = ["work1", "work2", "work3", "work4", "work5"]
    return pickle.loads(redis_connection().blpop(sub_queues)[1])

def status():
    try:
        redis_connection().info()
        return "ok"
    except Exception:
        return "ERROR"

class Job(metaclass=ABCMeta):
    @abstractmethod
    def do(self):
        pass

class SendInvite(object):
    def __init__(self, user):
        self.user = user

    def do(self):
        logger = conv.logger("SendInvite")
        template_string = """Hello $name,

Follow this link to get your invite to Recall:

    https://recall.calpaterson.com/verify-email/$email_key

Reply to this email if you have any trouble!
Cal"""
        template = Template(template_string)
        try:
            name = self.user["firstName"]
            fullname = name + " " + self.user["surname"]
        except KeyError:
            name = self.user["pseudonym"]
        body = template.substitute(
            name=name, email_key=self.user["email_key"])
        messages.email_(self.user["email"], "cal@calpaterson.com", body,
                        "Recall Invite")
        if "RECALL_TEST_MODE" not in conv.settings and\
                "RECALL_DEBUG_MODE" not in conv.settings:
            for number in conv.settings["RECALL_ALERT_PHONE_NUMBERS"].split(", "):
                messages.text(
                    number, "{fullname} ({email}) just signed up for Recall".format(
                        fullname=fullname, email=self.user["email"]))
        logger.info("Sent invite email to " + self.user["email"])

class IndexRecord(object):
    user_agent = "Recall (like Googlebot/2.1) - email cal@calpaterson.com for support"

    def __init__(self, record):
        self.record = record

    def may_fetch(self, hyperlink):
        url_obj = urlparse(hyperlink)
        robots_url = url_obj.scheme + "://" + url_obj.netloc + "/robots.txt"
        robots_parser = rerp.RobotExclusionRulesParser()
        robots_parser.user_agent = self.user_agent
        robots_parser.fetch(robots_url)
        allowed = robots_parser.is_allowed(self.user_agent, hyperlink)
        if not allowed:
            self.logger.warn("Not allowed to fetch " + hyperlink)
        return allowed

    def get_fulltext(self, mark):
        headers = {"User-Agent": self.user_agent}
        if "hyperlink" in mark and self.may_fetch(mark["hyperlink"]):
            response = requests.get(mark["hyperlink"], headers=headers)
            if response.status_code in range(200, 300):
                mark["£fulltext"] = BeautifulSoup(response.content).get_text()
            else:
                self.logger.warn("Requested {hyperlink}, but got {status_code}".format(
                        hyperlink=mark["hyperlink"],
                        status_code=response.status_code))


    def update_last_indexed_time(self, mark):
        mark["£last_indexed"] = int(time.time() * 1000)
        db = conv.db()
        db.marks.update(
            {"@": mark["@"], "~": mark["~"]},
            {"$set": {"£last_indexed": mark["£last_indexed"]},
             "$unset": "£q"})

    def mark_for_record(self, record):
        if ":" not in record:
            mark = record
        else:
            db = conv.db()
            mark = db.marks.find_one(
                {"@": record[":"]["@"], "~": record[":"]["~"]})
            del mark["_id"]
        return mark

    def do(self):
        self.logger = conv.logger("IndexRecord")
        mark = self.mark_for_record(self.record)
        self.update_last_indexed_time(mark)

        self.get_fulltext(mark)

        url = "http://{hostname}:{port}/{index}/{type}/{id}".format(
            hostname = conv.settings["RECALL_ELASTICSEARCH_HOST"],
            port = int(conv.settings["RECALL_ELASTICSEARCH_PORT"]),
            index = conv.settings["RECALL_ELASTICSEARCH_INDEX"],
            type = "mark",
            id = mark["@"] + str(mark["~"]))
        requests.post(url, data=json.dumps(mark))
        self.logger.info("Indexed {who}/{when}".format(
                who=mark["@"], when=mark["~"]))
