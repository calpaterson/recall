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
from copy import deepcopy
from pprint import pformat
from functools import wraps

import requests
import pymongo

settings = {}

def get_db():
    db_name = settings["RECALL_MONGODB_DB_NAME"]
    return pymongo.Connection(host=settings["RECALL_MONGODB_HOST"],
                              port=int(settings["RECALL_MONGODB_PORT"]))[db_name]

def load_settings():
    if "RECALL_DEBUG_MODE" in os.environ:
        settings.update({
                "RECALL_API_BASE_URL": "https://localhost:5000",
                "RECALL_API_HOST": "localhost",
                "RECALL_API_PORT": "5000",
                "RECALL_ELASTICSEARCH_HOST": "localhost",
                "RECALL_ELASTICSEARCH_PORT": "9200",
                "RECALL_ELASTICSEARCH_INDEX": "test",
                "RECALL_MARK_LIMIT": "100",
                "RECALL_MONGODB_DB_NAME": "recall",
                "RECALL_MONGODB_HOST": "localhost",
                "RECALL_MONGODB_PORT": "27017",
                "RECALL_REDIS_DB": "14",
                "RECALL_REDIS_HOST": "localhost",
                "RECALL_REDIS_PORT": "6379",
                })
        print "Using debug mode settings"
    else:
        for name in os.environ:
            if name.startswith("RECALL_"):
                settings[name] = os.environ[name]

def get_recall_server_api_url():
    return "http://" + settings["RECALL_API_HOST"] + ":" +\
        settings["RECALL_API_PORT"]

def get_es_base_url():
    return "http://" + settings["RECALL_ELASTICSEARCH_HOST"] + ":" +\
        settings["RECALL_ELASTICSEARCH_PORT"]

def get_es_mark_url():
    return "{es_base_url}/{index}/mark".format(
        es_base_url=get_es_base_url(),
        index=settings["RECALL_ELASTICSEARCH_INDEX"])


def wipe_mongodb():
    for collection_name in get_db().collection_names():
        if collection_name == u"system.indexes":
            continue
        get_db().drop_collection(collection_name)

def wipe_elastic_search():
    url = "{search_url}/{index}".format(
        search_url = get_es_base_url(),
        index = settings["RECALL_ELASTICSEARCH_INDEX"])
    requests.delete(url)

def post_mark(user, mark):
    url = get_recall_server_api_url() + "/mark"
    data = json.dumps(mark)
    headers = user.headers()
    headers["content-type"] = "application/json"
    return requests.post(url, data=data, headers=headers)

def get_linked(user, who, when):
    url = get_recall_server_api_url() + "/linked/" + who + "/" + str(when)
    response = requests.get(url, headers=user.headers())
    return json.loads(response.content)

def assert_marks_equal(marklist1, marklist2):
    if type(marklist1) == type(marklist2) == type({}):
        return assert_individual_marks_equal(marklist1, marklist2)
    key_function = lambda x: x["~"]
    sorted_marklist1 = sorted(marklist1, key=key_function)
    sorted_marklist2 = sorted(marklist2, key=key_function)
    for index in xrange(0, len(sorted_marklist1)):
        try:
            assert_individual_marks_equal(
                sorted_marklist1[index], sorted_marklist2[index])
        except IndexError:
            raise AssertionError("Marks not equal: \n%s\n%s" %
                                 (pformat(marklist1), pformat(marklist2)))


def assert_individual_marks_equal(mark1_, mark2_):
    field = None
    try:
        fields = mark1_.keys()
        fields += mark2_.keys()
        for field in set(fields):
            if type(field) == str or type(field) == unicode:
                if field.startswith(u"%") or field.startswith(u"£"):
                    continue
            assert field in mark1_
            assert field in mark2_
            assert mark1_[field] == mark2_[field]
    except AssertionError:
        raise AssertionError("Marks not equal: \n%s\n%s" %
                             (pformat(mark1_), pformat(mark2_)))

_test_user_counter = 1
def create_test_user():
    global _test_user_counter
    class User(object):
        email = None
        def __init__(self, pseudonym, email, password):
            self.pseudonym = pseudonym
            self.email = email
            self.password = password

        def headers(self):
            return {"x-email": self.email, "x-password": self.password}

    pseudonym = "example" + str(_test_user_counter)
    email = pseudonym + "@example.com"
    password = email
    post_data = json.dumps({"pseudonym": pseudonym, "email": email})
    url = get_recall_server_api_url() + "/user"
    requests.post(url, data=post_data,
                  headers={"content-type": "application/json"})
    _test_user_counter += 1

    email_key = get_db().users.find_one({"email": email})["email_key"]

    post_data = json.dumps({"password": password, "email": email})
    url = get_recall_server_api_url() + "/user/" + email_key
    requests.post(url, data=post_data,
                  headers={"content-type": "application/json"})
    return User(pseudonym, email, password)

def with_patience(test, seconds=5, gap=0.1):
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
        except:
            raise e

def on_json(f):
    def decorated(*args, **kwargs):
        assert len(args) == 1
        return json.dumps(f(json.loads(args[0]), **kwargs),
                          indent=4)
    return decorated
