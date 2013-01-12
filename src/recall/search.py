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

from pprint import pformat
from urllib.parse import urlparse
import json
import robotexclusionrulesparser as rerp
import time

import requests
from bs4 import BeautifulSoup
from redis import StrictRedis

from recall import messages, jobs
from recall import convenience as conv


def get_es_base_url():
    return "http://" + conv.settings["RECALL_ELASTICSEARCH_HOST"] + ":" +\
        conv.settings["RECALL_ELASTICSEARCH_PORT"]

def get_es_mark_url():
    return "{es_base_url}/{index}/mark".format(
        es_base_url=get_es_base_url(),
        index=conv.settings["RECALL_ELASTICSEARCH_INDEX"])

def set_mapping():
    response = requests.put(get_es_mark_url() + "/_mapping",
                            data=json.dumps(mapping))

mapping = {
    "mark": {
        "properties": {
            "~": {
                "type": "long",
                "store": "yes",
                "index": "yes"},
            "@": {
                "index": "not_analyzed"}}}}

def clear():
    url = "{search_url}/{index}".format(
        search_url = get_es_base_url(),
        index = conv.settings["RECALL_ELASTICSEARCH_INDEX"])
    requests.delete(url)

class IncoherentSearchQueryException(Exception):
    pass

class SearchQueryBuilder(object):

    def __init__(self):
        self.of_size(10)
        self.as_user_set = False
        self.filters = []
        self.queries = []
        self.sort = None

    def with_keywords(self, string):
        self.queries.append({"match": {"_all": string}})
        return self

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

    def only_user(self, user):
        at_sign_workaround = user["email"].split("@")[0]
        self.filters.append(
            {"term": {"@": at_sign_workaround}})
        return self

    def the_url(self, url):
        self.queries.append({"match": { "hyperlink": url}})
        return self

    def anonymously(self):
        if self.as_user_set:
            raise IncoherentSearchQueryException(
                "Tried to search anonymously but user has already been set")
        self.as_user_set = True
        self.filters.append({"not": {"term": {"%private": True}}})
        return self

    def sort_by_when(self):
        self.sort = [{"~": {"order": "desc"}}]
        return self

    def build(self):
        query_and_filters = {
            "filter": {"and": self.filters,}
            }
        if self.queries == []:
            query_and_filters.update({"query": {"match_all": {}}})
        else:
            query_and_filters.update(
                {"query": {"bool": {
                            "must": self.queries
                            }}})
        query = {
            "size": self.size,
            "query":{
                "filtered": query_and_filters
                }
            }
        if self.sort is not None:
            query["sort"] = self.sort
        return query

    def __str__(self):
        return pformat(self.build())

def status():
    try:
        if requests.get(get_es_base_url()).json["ok"]:
            return "ok"
        else:
            return "ERROR"
    except Exception as e:
        return "ERROR"

def search(queryBuilder):
    response = requests.get(get_es_mark_url() +  "/_search?",
                            data=json.dumps(queryBuilder.build()))
    marks = []
    try:
        for mark in response.json["hits"]["hits"]:
            marks.append(mark["_source"])
    except KeyError:
        conv.logger("search").exception("Elasticsearch error: " + str(response.json))
    return response.json["hits"]["total"], marks

class IndexRecord(jobs.Job):
    """Index a record (part of a mark) in elasticsearch"""
    user_agent = "Recall - email cal@calpaterson.com for support"

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
        try:
            headers = {"User-Agent": self.user_agent}
            if "hyperlink" in mark and self.may_fetch(mark["hyperlink"]):
                response = requests.get(mark["hyperlink"], headers=headers)
                if response.status_code in range(200, 300):
                    mark["£fulltext"] = BeautifulSoup(response.content).get_text()
                else:
                    self.logger.warn("Requested {hyperlink}, but got {status_code}".format(
                        hyperlink=mark["hyperlink"],
                        status_code=response.status_code))
        except Exception as e:
            try:
                status_code = response.status_code
            except NameError:
                status_code = None
            self.logger.exception("Error while getting fulltext" + repr({
                "hyperlink": mark["hyperlink"],
                "response_status": status_code}))


    def update_last_indexed_time(self, mark):
        mark["£last_indexed"] = int(time.time())
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
