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
import os
import sys
import time
import traceback
import uuid
from wsgiref.simple_server import make_server

from flask import Flask, request, make_response, Response, g
from pymongo import Connection, DESCENDING, ASCENDING
from redis import Redis
import bcrypt
import requests

import convenience

app = Flask(__name__)

settings = convenience.settings

class HTTPException(Exception):
    def __init__(self, message, status_code, machine_readable=None):
        self.message = message
        self.status_code = status_code
        self.machine_readable = machine_readable

def handle_exception(exception):
    if "RECALL_TEST_MODE" in settings:
        print >> sys.stderr, traceback.format_exc(),
    def json_error(message):
        document = {"human_readable": message}
        if hasattr(exception, "machine_readable") and \
                exception.machine_readable is not None:
            document["machine_readable"] = exception.machine_readable
        return json.dumps(document)

    if isinstance(exception, HTTPException):
        return json_error(exception.message), exception.status_code
    if isinstance(exception, AssertionError):
        return json_error(exception.message), 400
    else:
        return json_error("Unknown exception: " + exception.message), 500

app.handle_exception = handle_exception

def has_no_problematic_keys(mark):
    mark_queue = []
    current = mark
    while True:
        for key in current:
            if key.startswith("$") or key.startswith(u"£"):
                raise HTTPException(
                    "Mark keys may not be prefixed with $ or £", 400,
                    machine_readable=key)
            if isinstance(current[key], dict):
                mark_queue.insert(0, current[key])
        if mark_queue == []:
            return
        else:
            current = mark_queue.pop()

def whitelist(dict_, whitelist):
    d = {}
    for k, v in dict_.items():
        if k in whitelist:
            d[k] = v
    return d

def blacklist(dict_, blacklist):
    d = {}
    for k, v in dict_.items():
        if k not in blacklist:
            d[k] = v
    return d

def json_error(message):
    return json.dumps({"error": message})

def unixtime():
    if app.testing:
        return 0
    else:
        return int(time.time())

@app.before_request
def authentication():
    try:
        email = request.headers["X-Email"]
        password = request.headers["X-Password"]
        g.user = convenience.db().users.find_one(
            {"email": email, "password_hash": {"$exists": True}})
        assert g.user["password_hash"] == bcrypt.hashpw(
            password, g.user["password_hash"])
    except (KeyError, TypeError):
        g.user = None
    except AssertionError:
        raise HTTPException("Email or password or both do not match", 403)

def require_authentication(f):
    def decorated(*args, **kwargs):
        if g.user is None:
            raise HTTPException("You must include authentication headers", 400)
        return f(*args, **kwargs)
    return decorated

def make_mark_url(mark):
    return settings["RECALL_API_BASE_URL"] + "/mark/" \
        + mark[u"@"] + "/" + str(int(mark["~"]))

@app.route("/mark", methods=["POST"])
@require_authentication
def add_marks():
    def insert_mark(body):
        assert "~" in body and "@" in body, "Must include @ and ~ with all marks"
        has_no_problematic_keys(body)
        body[u"£created"] = unixtime()
        convenience.db().marks.insert(body)
        del body["_id"]
        convenience.redis_connection().lpush("marks", json.dumps(body))
        return body

    marks = json.loads(request.data)

    if type(marks) == dict:
        marks = [marks]
    try:
        for mark in marks:
            assert "@" in mark
            assert "~" in mark
    except AssertionError:
        raise HTTPException("Must include @ and ~ with all marks", 400)

    for mark in marks:
        insert_mark(mark)
    return "null", 202

@app.route("/mark", methods=["GET"])
def get_all_marks():
    def split_tags(tag_string):
        tags = tag_string.split(" ")
        return tags if tags != [""] else []
    if "q" in request.args:
        query = SearchQueryBuilder()
        query.with_keywords(request.args["q"])
        if g.user is not None:
            query.as_user(g.user)
        else:
            query.anonymously()

        for tag in split_tags(request.args.get("about", "")):
            query.about(tag)
        for tag in split_tags(request.args.get("not_about", "")):
            query.not_about(tag)

        url = convenience.get_es_mark_url() +  "/_search?"
        r = requests.get(url, data=json.dumps(query.build()))
        return results_to_marks(r.content)
    else:
        return marks()

@app.route("/mark/<email>", methods=["GET"])
def get_all_marks_by_email(email):
    spec_additions = {"@": email}
    return marks(spec_additions)

@convenience.on_json
def results_to_marks(body):
    marks = []
    try:
        for mark in body["hits"]["hits"]:
            marks.append(mark["_source"])
        return marks
    except KeyError:
        raise HTTPException("no results", 404)

class SearchQueryBuilder(object):
    class IncoherentSearchQueryException(Exception):
        pass

    def __init__(self):
        self.of_size(100)
        self.as_user_set = False
        self.filters = []

    def with_keywords(self, string):
        self.query_string = {"text": {"_all": string}}
        return self

    # def respecting_privacy(self):
    #     self.filters = [
    #             {"not": {"term": {"%private": True}}}
    #             ]
    #     return self

    def of_size(self, size):
        self.size = size
        return self

    def about(self, tag):
        self.filters.append({"term": {"about": tag}})
        return self

    def not_about(self, tag):
        self.filters.append({"not": {"term": {"about": tag}}})
        return self

    def as_user(self, user):
        if self.as_user_set:
            raise IncoherentSearchQueryException(
                "Tried to search as user but already anonymous")
        self.as_user_set = True
        # Have not worked out how to correctly escape @ for elasticsearch
        at_sign_workaround = user["email"].split("@")[0]
        self.filters.append(
            {"or": [
                    {"term": {"@": at_sign_workaround}},
                    {"not": {"term": {"%private": True}}}]})
        return self

    def anonymously(self):
        if self.as_user_set:
            raise IncoherentSearchQueryException(
                "Tried to search anonymously but user has already been set")
        self.as_user_set = True
        self.filters.append({"not": {"term": {"%private": True}}})
        return self

    def build(self):
        return {
            "size": self.size,
            "query":{
                "filtered":{
                    "query": self.query_string,
                    "filter": {"and": self.filters,}
                    }
                }
            }

def marks(spec_additions={}):
    spec = _build_spec(spec_additions)
    limit = int(request.args.get("maximum", 0))
    rs = convenience.db().marks.find(spec, sort=[("~", DESCENDING)],
                         limit=limit)
    marks = []
    counter = 0
    for mark in rs:
        del(mark[u"_id"])
        marks.append(mark)
        mark[u"%url"] = make_mark_url(mark)
        counter += 1
        if counter > settings["RECALL_MARK_LIMIT"]:
            raise HTTPException(
                "May not request more than %s marks at once"
                % settings["RECALL_MARK_LIMIT"],
                413, machine_readable=settings["RECALL_MARK_LIMIT"])
    return json.dumps(marks)

def _build_spec(spec_additions):
    spec = {}
    _respect_privacy(spec)

    if int(request.args.get("since", 0)) != 0:
        spec["~"] = {"$gt": int(request.args.get("since", 0))}
    if int(request.args.get("before", 0)) != 0:
        spec["~"] = {"$lt": int(request.args.get("before", 0))}
    spec.update(spec_additions)
    return spec

def _respect_privacy(spec):
    if g.user:
        spec.update({"$or": [
                {"@": g.user["email"]},
                {"%private": {"$exists": False}}]})
    else:
        spec.update({"%private": {"$exists": False}})

@app.route("/mark/<email>/<time>", methods=["GET"])
def get_mark(email, time):
    spec = {"%private": {"$exists": False},
            "@": email,
            "~": int(time)}
    try:
        if g.user:
            spec = {"$or": [
                    {"@": g.user["email"]},
                    {"%private": {"$exists" : False}}
                    ]}
            spec.update({"~": int(time)})
    except KeyError:
        pass
    mark = convenience.db().marks.find_one(spec)
    try:
        del(mark[u"_id"])
        mark[u"%url"] = make_mark_url(mark)
    except TypeError:
        return json_error("No such mark found"), 404
    return json.dumps(mark), 200

@app.route("/user/<email>", methods=["GET"])
def user(email):
    users = convenience.db().users
    user = users.find_one({"email": email})
    if user is None:
        return "null", 404

    return_value = whitelist(user, [
            "pseudonym",
            "firstName",
            "surname",
            "email"])
    if g.user == user:
        return_value["self"] = True
    return json.dumps(return_value), 200

@app.route("/user", methods=["POST"])
def request_invite():
    body = whitelist(json.loads(request.data), [
            "pseudonym",
            "firstName",
            "surname",
            "email",
            ])
    if "email" not in body:
        return "You must provide an email field", 400
    body["email_key"] = str(uuid.uuid4())
    body["registered"] = unixtime()
    convenience.db().users.ensure_index("email", unique=True)
    convenience.db().users.insert(body, safe=True)
    return "null", 202

@app.route("/user/<email_key>", methods=["POST"])
def verify_email(email_key):
    if "RECALL_TEST_MODE" in settings or "RECALL_DEBUG_MODE" in settings:
        salt = bcrypt.gensalt(1)
    else:
        salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(json.loads(request.data)["password"], salt)

    spec = {"email_key": email_key, "email": json.loads(request.data)["email"],
            "verified": {"$exists": False}}
    update = {"$set": {"password_hash": password_hash,
                       "verified": unixtime()}}
    success = convenience.db().users.update(spec, update, safe=True)["updatedExisting"]
    if not success:
        if convenience.db().users.find_one({"email_key": email_key, "email": json.loads(request.data)["email"]}):
            raise HTTPException("Already verified", 403)
        else:
            raise HTTPException("No such email_key or wrong email", 404)
    user = convenience.db().users.find_one({"email_key": email_key})
    return json.dumps(blacklist(
            user, ["_id", "email_key", "password_hash"])), 201

@app.route("/linked/<who>/<when>", methods=["GET"])
def linked(who, when):
    spec = {"$or": [
            {"%private": {"$exists": False},
             "@": who,
             "~": int(when)},
            {"%private": {"$exists": False},
             u":.@": who,
             u":.~": int(when)
             }
            ]}
    found = []
    for mark in convenience.db().marks.find(spec).sort(":", ASCENDING):
        del(mark[u"_id"])
        mark[u"%url"] = make_mark_url(mark)
        found.append(mark)
    return json.dumps(list(found))

if __name__ == "__main__":
    convenience.load_settings()
    http_server = make_server("", int(settings["RECALL_API_PORT"]), app)
    http_server.serve_forever()