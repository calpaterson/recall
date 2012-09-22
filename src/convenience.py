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
import json
import time
import sys
from copy import deepcopy
from pprint import pformat
from functools import wraps
import logging

from redis import Redis
import requests
import pymongo

settings = {}

def db():
    db_name = settings["RECALL_MONGODB_DB_NAME"]
    return pymongo.Connection(
        settings["RECALL_MONGODB_HOST"],
        int(settings["RECALL_MONGODB_PORT"]))[db_name]


def logger(name):
    fmt = "%(levelname)s:%(asctime)s:%(name)s:%(process)d:%(message)s"
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt))
    logger = logging.getLogger(name)
    if "RECALL_DEBUG_MODE" in settings or "RECALL_TEST_MODE" in settings:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger


def redis_connection():
    return Redis(
        host=settings["RECALL_REDIS_HOST"],
        port=int(settings["RECALL_REDIS_PORT"]),
        db=int(settings["RECALL_REDIS_DB"]))

def load_settings():
    if "RECALL_DEBUG_MODE" in os.environ:
        settings.update({
                "RECALL_API_BASE_URL": "https://localhost:7777",
                "RECALL_API_HOST": "localhost",
                "RECALL_API_PORT": "7777",
                "RECALL_ELASTICSEARCH_HOST": "localhost",
                "RECALL_ELASTICSEARCH_PORT": "9200",
                "RECALL_ELASTICSEARCH_INDEX": "recalldebug",
                "RECALL_MARK_LIMIT": "100",
                "RECALL_MONGODB_DB_NAME": "recalldebug",
                "RECALL_MONGODB_HOST": "localhost",
                "RECALL_MONGODB_PORT": "27017",
                "RECALL_REDIS_DB": "7",
                "RECALL_REDIS_HOST": "localhost",
                "RECALL_REDIS_PORT": "6379",
                "RECALL_DEBUG_MODE": "true"
                })
        print "Using debug mode settings"
    elif "RECALL_TEST_MODE" in os.environ:
        settings.update({
                "RECALL_API_BASE_URL": "https://localhost:6666",
                "RECALL_API_HOST": "localhost",
                "RECALL_API_PORT": "6666",
                "RECALL_ELASTICSEARCH_HOST": "localhost",
                "RECALL_ELASTICSEARCH_PORT": "9200",
                "RECALL_ELASTICSEARCH_INDEX": "recalltest",
                "RECALL_MARK_LIMIT": "100",
                "RECALL_MONGODB_DB_NAME": "test",
                "RECALL_MONGODB_HOST": "localhost",
                "RECALL_MONGODB_PORT": "27017",
                "RECALL_REDIS_DB": "6",
                "RECALL_REDIS_HOST": "localhost",
                "RECALL_REDIS_PORT": "6379",
                "RECALL_TEST_MODE": "true"
                })
        print "Using test mode settings"
    else:
        for name in os.environ:
            if name.startswith("RECALL_"):
                settings[name] = os.environ[name]

def api_url():
    return "http://" + settings["RECALL_API_HOST"] + ":" +\
        settings["RECALL_API_PORT"] + "/v1"

def new_url():
    return "http://" + settings["RECALL_API_HOST"] + ":" +\
        settings["RECALL_API_PORT"] + "/"

def get_es_base_url():
    return "http://" + settings["RECALL_ELASTICSEARCH_HOST"] + ":" +\
        settings["RECALL_ELASTICSEARCH_PORT"]

def get_es_mark_url():
    return "{es_base_url}/{index}/mark".format(
        es_base_url=get_es_base_url(),
        index=settings["RECALL_ELASTICSEARCH_INDEX"])

def wipe_mongodb():
    for collection_name in db().collection_names():
        if collection_name == u"system.indexes":
            continue
        db().drop_collection(collection_name)

def wipe_elastic_search():
    url = "{search_url}/{index}".format(
        search_url = get_es_base_url(),
        index = settings["RECALL_ELASTICSEARCH_INDEX"])
    requests.delete(url)

def wipe_redis():
    pass

def post_mark(user, mark):
    url = api_url() + "/mark"
    data = json.dumps(mark)
    headers = user.headers()
    headers["content-type"] = "application/json"
    response = requests.post(url, data=data, headers=headers)
    return response

def get_linked(user, who, when):
    url = api_url() + "/linked/" + who + "/" + str(when)
    response = requests.get(url, headers=user.headers())
    return json.loads(response.content)

def assert_marks_equal(marklist1, marklist2):
    try:
        if type(marklist1) == type(marklist2) == type({}):
            return _assert_individual_marks_equal(marklist1, marklist2)
        assert len(marklist1) == len(marklist2)
        key_function = lambda x: x["~"]
        sorted_marklist1 = sorted(marklist1, key=key_function)
        sorted_marklist2 = sorted(marklist2, key=key_function)
        for index in xrange(0, len(sorted_marklist1)):
            _assert_individual_marks_equal(
                sorted_marklist1[index], sorted_marklist2[index])
    except AssertionError:
        raise AssertionError(
            "Marks not equal (percent and pound fields ignored): \n%s\n%s" %
            (pformat(marklist1), pformat(marklist2)))


def _assert_individual_marks_equal(mark1_, mark2_):
    field = None
    fields = mark1_.keys()
    fields += mark2_.keys()
    for field in set(fields):
        if type(field) == str or type(field) == unicode:
            if field.startswith(u"%") or field.startswith(u"£"):
                continue
        assert field in mark1_
        assert field in mark2_
        assert mark1_[field] == mark2_[field]

_test_user_counter = 1
def create_test_user(fixture_user=False):
    if fixture_user:
        pseudonym = email = password = "example@example.com"
    else:
        global _test_user_counter
        pseudonym = "example" + str(_test_user_counter)
        email = password = pseudonym + "@example.com"
        _test_user_counter += 1

    class User(object):
        email = None
        def __init__(self, pseudonym, email, password):
            self.pseudonym = pseudonym
            self.email = email
            self.password = password

        def headers(self):
            return {"x-email": self.email, "x-password": self.password}

    post_data = json.dumps({"pseudonym": pseudonym, "email": email})
    url = new_url() + "people/" + email + "/"
    requests.post(url, data=post_data,
                  headers={"content-type": "application/json"})

    email_key = db().users.find_one({"email": email})["email_key"]

    post_data = json.dumps({"password": password, "email": email})
    url = new_url() + "people/" + email + "/" + email_key
    requests.post(url, data=post_data,
                  headers={"content-type": "application/json"})
    return User(pseudonym, email, password)

def with_patience(test, seconds=7, gap=0.1):
    give_up = int(time.time()) + seconds
    while(True):
        try:
            test()
            break
        except AssertionError as e:
            now = int(time.time())
            if now < give_up:
                time.sleep(gap)
                continue
            else:
                raise e
        except Exception:
            raise

def unixtime():
    if "RECALL_TEST_MODE" in settings:
        return 0
    else:
        return int(time.time())

def on_json(f):
    def decorated(*args, **kwargs):
        assert len(args) == 1
        return json.dumps(f(json.loads(args[0]), **kwargs),
                          indent=4)
    return decorated
