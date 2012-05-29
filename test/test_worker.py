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
import time

import requests

import convenience

class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.tearDown()

    def tearDown(self):
        convenience.wipe_mongodb()
        convenience.wipe_elastic_search()

    def test_will_index_new_trees(self):
        user = convenience.create_test_user()
        mark = {"@": user.email, "~": 0, "#": "Please index me!"}
        convenience.post_mark(user, mark)

        def check_was_indexed():
            url = convenience.get_search_api_url() + "/test/mark/%s%s" % (
                user.email, "0")
            response = requests.get(url)
            self.assertIn("_source", response.content)
            tree = json.loads(response.content)["_source"]
            self.assertEquals(response.status_code, 200)
            convenience.assert_marks_equal(tree, mark, self)

        convenience.keep_trying(check_was_indexed)
        

if __name__ == "__main__":
    unittest.main()
