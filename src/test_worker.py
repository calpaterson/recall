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

    def test_will_index_new_roots(self):
        user = convenience.create_test_user()
        mark = {"@": user.email, "~": 0, "#": "Please index me!"}
        convenience.post_mark(
            user, mark)
        convenience.wipe_mongodb()

        def inner_assert():
            url = convenience.get_recall_server_api_url()
            url += "/mark?q=index"
            response = requests.get(url)
            content = json.loads(response.content)
            self.assertEquals(200, response.status_code)
            self.assertEquals(1, len(content))
            convenience.assert_marks_equal(content[0], mark)

        convenience.with_patience(inner_assert)

    @unittest.expectedFailure
    def test_will_index_trees(self):
        user = convenience.create_test_user()
        map(lambda mark: convenience.post_mark(user, mark), [
                {"@": user.email, "~": 0, "#": "Please index me!"},
                {"@": user.email, "~": 1, "about": "hopes"},
                {"@": user.email, "~": 2, "about": "pleads"},
                ])
        expected_tree = {
            "@": user.email,
            "#": "Please index me!",
            "~": 0,
            "about": ["hopes", "pleads"]}
        convenience.with_patience(lambda: self._assert_index(
                user.email + "0", expected_tree))

if __name__ == "__main__":
    unittest.main()
