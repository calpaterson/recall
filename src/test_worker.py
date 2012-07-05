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

    def test_can_search_for_marks(self):
        user = convenience.create_test_user()
        mark = {"@": user.email, "~": 0, "#": "Please index me!"}
        convenience.post_mark(
            user, mark)

        def inner_assert():
            url = convenience.get_recall_server_api_url()
            url += "/mark?q=index"
            response = requests.get(url)
            content = json.loads(response.content)
            self.assertEquals(200, response.status_code)
            self.assertEquals(1, len(content))
            convenience.assert_marks_equal(content, [mark])

        convenience.with_patience(inner_assert)

    def test_cant_search_for_private_marks_anonymously(self):
        user = convenience.create_test_user()
        mark1 = {"@": user.email, "~": 0, "#": "Khajiit has no words for you", "%private": True}
        mark2 = {"@": user.email, "~": 0, "#": "Khajiit has some words for you"}
        convenience.post_mark(user, mark1)
        convenience.post_mark(user, mark2)


        url = convenience.get_recall_server_api_url()
        url += "/mark1?q=Khajiit"

        def inner_assert():
            response = requests.get(url, headers=user.headers())
            content = json.loads(response.content)
            self.assertEquals(200, response.status_code)
            self.assertEquals([mark2], content)

        convenience.with_patience(inner_assert)

    def test_cant_search_for_private_marks_anonymously(self):
        user1 = convenience.create_test_user()
        user2 = convenience.create_test_user()
        mark1 = {"@": user1.email, "~": 0, "#": "My secret mark", "%private": True}
        mark2 = {u"@": user2.email, u"~": 0, u"#": u"Someone else's secret mark"}
        r1 = convenience.post_mark(user1, mark1)
        r2 = convenience.post_mark(user2, mark2)

        url = convenience.get_recall_server_api_url()
        url += "/mark?q=secret"

        def inner_assert():
            response = requests.get(url, headers=user2.headers())
            content = json.loads(response.content)
            self.assertEquals(200, response.status_code)
            convenience.assert_marks_equal([mark2], content)

        convenience.with_patience(inner_assert)

if __name__ == "__main__":
    unittest.main()
