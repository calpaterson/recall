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

import pickle
from string import Template
from abc import ABCMeta, abstractmethod

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

    def __getstate__(self):
        state = self.__dict__.copy()
        if "logger" in state:
            del state['logger']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.logger = conv.logger(self.__class__.__name__)

class SendInvite(object):
    def __init__(self, user):
        self.user = user

    def do(self):
        logger = conv.logger("SendInvite")
        template_string = """Hello $name,

Follow this link to get your invite to Recall:

    $scheme://$host/people/verify-email/$email_key

Reply to this email if you have any trouble!
Cal"""
        template = Template(template_string)
        try:
            name = self.user["firstName"]
            fullname = name + " " + self.user["surname"]
        except KeyError:
            name = self.user["pseudonym"]
        body = template.substitute(
            host=conv.settings["RECALL_API_HOST"],
            scheme="http",
            name=name,
            email_key=self.user["email_key"])
        messages.email_(self.user["email"], "cal@calpaterson.com", body,
                        "Recall Invite")
        if "RECALL_TEST_MODE" not in conv.settings and\
                "RECALL_DEBUG_MODE" not in conv.settings:
            for number in conv.settings["RECALL_ALERT_PHONE_NUMBERS"].split(", "):
                messages.text(
                    number, "{fullname} ({email}) just signed up for Recall".format(
                        fullname=fullname, email=self.user["email"]))
        logger.info("Sent invite email to " + self.user["email"])
