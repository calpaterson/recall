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

from __future__ import absolute_import

import json
from pprint import pformat

import requests

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
        self.query_string = None
        self.sort = None

    def with_keywords(self, string):
        self.query_string = {"text": {"_all": string}}
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
        if self.query_string is None:
            query_and_filters.update({"query": {"match_all": {}}})
        else:
            query_and_filters.update({"query": self.query_string})
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


