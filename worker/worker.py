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
import logging

import requests
from redis import Redis

_settings = {}

def load_settings():
    for name in os.environ:
        if name.startswith("RECALL_"):
            _settings[name] = os.environ[name]

def indexTrees():
    search_engine_url = "http://%s:%s/%s" % (
        _settings["RECALL_ELASTICSEARCH_HOST"],
        int(_settings["RECALL_ELASTICSEARCH_PORT"]),
        _settings["RECALL_ELASTICSEARCH_INDEX"])
    
    recall_server_api_url = "http://%s:%s" % (
        _settings["RECALL_SERVER_HOST"],
        int(_settings["RECALL_SERVER_PORT"]))
    
    connection = Redis(
        host=_settings["RECALL_REDIS_HOST"],
        port=int(_settings["RECALL_REDIS_PORT"]),
        db=int(_settings["RECALL_REDIS_DB"]))
    
    mark = connection.blpop("marks")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    load_settings()
    while(True):
        indexTrees()
