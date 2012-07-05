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
from convenience import settings

class LowLevelMarkAPITests(unittest.TestCase):
    def setUp(self):
        convenience.load_settings()

    def tearDown(self):
        convenience.wipe_mongodb();

    def test_save_and_retrieve_fact(self):
        user = convenience.create_test_user()
        mark = {u"#": "Hello", u"~": 0, u"@": user.email}
        fact = {u":": {u"~": 0, u"@": user.email},
                u"about": u"greeting",
                u"@": user.email,
                u"~": 1
                }

        convenience.post_mark(user, mark)
        convenience.post_mark(user, fact)

        marks = convenience.get_linked(user, user.email, 0)
        self.assertEquals(2, len(marks))
        convenience.assert_marks_equal(marks[0], mark)
        convenience.assert_marks_equal(marks[1], fact)
