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

settings = {}

def load_settings():
    settings["RECALL_SERVER_HOST"] = os.environ.get(
        "RECALL_SERVER_HOST", "localhost")
    settings["RECALL_SERVER_PORT"] = os.environ.get(
        "RECALL_SERVER_PORT", 5000)

    settings["RECALL_ELASTICSEARCH_PORT"] = os.environ.get(
        "RECALL_ELASTICSEARCH_PORT", 9200)
    settings["RECALL_ELASTICSEARCH_HOST"] = os.environ.get(
        "RECALL_ELASTICSEARCH_HOST", "localhost")

    settings["RECALL_SERVER_EMAIL"] = os.environ.get(
        "RECALL_SERVER_HOST")
    settings["RECALL_SERVER_PASSWORD"] = os.environ.get(
        "RECALL_SERVER_PASSWORD")

def indexTrees():
    search_engine_url = "http://%s:%s" % (
        settings["RECALL_ELASTICSEARCH_HOST"],
        settings["RECALL_ELASTICSEARCH_PORT"])

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    load_settings()
    while(True):
        indexTrees()
