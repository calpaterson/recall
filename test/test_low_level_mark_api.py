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
import unittest
import json

import pymongo
import requests

import convenience

_settings = {
    "RECALL_SERVER_HOST": os.environ.get("RECALL_SERVER_HOST", "localhost"),
    "RECALL_SERVER_PORT": os.environ.get("RECALL_SERVER_PORT", 5001),
    }

class LowLevelMarkAPITests(unittest.TestCase):
    def setUp(self):
        self.recall_api_url = "http://" + _settings["RECALL_SERVER_HOST"] +\
            ":" + _settings["RECALL_SERVER_PORT"]

    def tearDown(self):
        convenience.wipe_mongodb();

    @unittest.expectedFailure
    def test_save_and_retrieve_fact(self):
        user = self.create_test_user()
        mark = {u"#": "Hello", u"~": 0, u"@": user.email}
        fact = {u":": {u"~": 0, u"@": user.email},
                u"about": u"greeting",
                u"@": user.email,
                u"~": 1
                }

        self.post_mark(user, mark)
        self.post_mark(user, fact)

        marks = self.get_linked(user, user.email, 0)
        self.assertEquals(2, len(marks))
        self.assert_marks_equal(marks[0], mark)
        self.assert_marks_equal(marks[1], fact)
