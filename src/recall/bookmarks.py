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



from bottle import abort, request, Bottle, response

from recall import plugins
from recall import convenience as conv
from recall import search
from recall import jobs

from bs4 import BeautifulSoup

logger = conv.logger("bookmarks")

app = Bottle()
app.install(plugins.ppjson)
app.install(plugins.auth)
app.install(plugins.cors)
app.error_handler = plugins.handler_dict

def has_problematic_keys(mark):
    mark_queue = []
    current = mark
    while True:
        for key in current:
            if key.startswith("$") or key.startswith("£"):
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
    if request.json["@"] != who or who != user["email"]:
        abort(400, "You may only add bookmarks as yourself")
    if request.json["~"] != int(when):
        abort(400, "You must use the same time in the bookmark as you post to")
    if has_problematic_keys(request.json):
        abort(400, "Bookmarks must not have keys prefixed with $ or £")
    request.json["£created"] = conv.unixtime()
    conv.db().bookmarks.insert(request.json)
    del request.json["_id"]
    jobs.enqueue(jobs.IndexRecord(request.json), priority=1)
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
    total, results = search.search(query)
    response.set_header("X-Recall-Total", total)
    if results == []:
        response.status = 404
    return results

@app.get("/<who>/all/")
def user_all_bookmarks(who, user):
    if who != user["email"]:
        abort(400, "You may only look at your own bookmarks")
    query = search.SearchQueryBuilder()
    if "q" in request.params:
        query.with_keywords(request.params["q"])
    query.as_user(user)
    total, results = search.search(query)
    if results == []:
        response.status = 404
    return results

@app.route("/<who>/", method="PATCH")
def import_(who, user):
    soup = BeautifulSoup(request.body)
    if soup.contents[0] != "NETSCAPE-Bookmark-file-1":
        abort(400, "You must send a bookmark file with the doctype " +
              " 'NETSCAPE-Bookmarks-file-1'")
    anchors = soup.find_all("a")
    bookmarks = []
    add_dates = set()
    for anchor in anchors:
        bookmark = {
            "~": int(anchor.attrs.get("add_date", conv.unixtime()))
            }
        while bookmark["~"] in add_dates:
            bookmark["~"] += 1
        add_dates.add(bookmark["~"])
        bookmark["hyperlink"] = anchor.attrs["href"]
        if bookmark["hyperlink"].startswith("place"):
            continue
        bookmark["title"] = anchor.string
        bookmark["@"] = user["email"]
        bookmark["%private"] = True
        bookmark["£created"] = conv.unixtime()
        bookmarks.append(bookmark)
    for each in bookmarks:
        conv.db().eachs.insert(each)
        del each["_id"]
        jobs.enqueue(jobs.IndexRecord(each), priority=1)
    response.status = 202

@app.get("/<who>/all/recent/")
def recent(who, user):
    if who != user["email"]:
        abort(400, "You may only look at your own bookmarks")
    total, hits = search.search(search.SearchQueryBuilder()
                                .sort_by_when()
                                .of_size(75)
                                .as_user(user)
                                .only_user(user))
    response.set_header("X-Recall-Total", total)
    return hits

#### NOT IMPLEMENTED:

@app.get("/<unused_who>/public/")
def user_public_bookmarks(unused_who):
    abort(501)

@app.get("/public/url/<unused_url:re:.*>")
def url(unused_url):
    abort(501)

# @app.post("/<who>/<when>/edits/<who_edited>/<time_editted/")
# def update(unused_who, unused_when, unused_who_edited, unused_time_editted):
#     abort(501)
