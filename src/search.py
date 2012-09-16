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

import requests

import convenience as conv

class SearchQueryBuilder(object):
    class IncoherentSearchQueryException(Exception):
        pass

    def __init__(self):
        self.of_size(100)
        self.as_user_set = False
        self.filters = []
        self.query_string = {"text": {"_all": ""}}

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

def search(queryBuilder):
    response = requests.get(conv.get_es_mark_url() +  "/_search?",
                            data=json.dumps(queryBuilder.build()))
    marks = []
    for mark in response.json["hits"]["hits"]:
        marks.append(mark["_source"])
    return marks
