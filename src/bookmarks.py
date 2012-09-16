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

from bottle import abort, request, Bottle, response
import requests

import plugins
import convenience as conv
import search

app = Bottle()
app.install(plugins.ppjson)
app.install(plugins.auth)
app.error_handler = plugins.PretendHandlerDict()

def has_problematic_keys(mark):
    mark_queue = []
    current = mark
    while True:
        for key in current:
            if key.startswith("$") or key.startswith(u"£"):
                return True
            if isinstance(current[key], dict):
                mark_queue.insert(0, current[key])
        if mark_queue == []:
            return False
        else:
            current = mark_queue.pop()

@app.post("/<who>/public/<when>/")
def add_public(who, when, user):
    if "~" not in request.json or "@" not in request.json:
        abort(400, "You must include @ and ~ with all bookmarks")
    if has_problematic_keys(request.json):
        abort(400, "Bookmarks must not have keys prefixed with $ or £")
    request.json[u"£created"] = conv.unixtime()
    conv.db().bookmarks.insert(request.json)
    del request.json["_id"]
    conv.redis_connection().lpush("bookmarks", json.dumps(request.json))
    response.status = 202

@app.post("/<who>/private/<when>/")
def add_private(who, when, user):
    request.json["%private"] = True
    add_public(who, when, user)

@app.get("/public/")
def public_bookmarks():
    query = search.SearchQueryBuilder()
    if "q" in request.params:
        query.with_keywords(request.params["q"])
    query.anonymously()
    results = search.search(query)
    if results == []:
        response.status = 404
    return results

@app.get("/<who>/all/")
def user_all_bookmarks(who, user):
    query = search.SearchQueryBuilder()
    if "q" in request.params:
        query.with_keywords(request.params["q"])
    query.as_user(user)
    results = search.search(query)
    if results == []:
        response.status = 404
    return results

#### NOT IMPLEMENTED:

@app.get("/<who>/public/")
def user_public_bookmarks(who):
    abort(501)

@app.get("/<who>/all/recent/")
def recent(who, user):
    abort(501)

@app.get("/public/url/<url>/")
def url(url):
    abort(501)

@app.route("/<who>/", method="PATCH")
def import_(who):
    abort(501)

@app.post("/<who>/<when>/edits/<who_edited>/<time_editted/")
def update(who, when, who_edited, time_editted):
    abort(501)
