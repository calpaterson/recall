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

import requests
from redis import Redis

import convenience

class WorkerTests(unittest.TestCase):
    def tearDown(self):
        convenience.wipe_mongodb

    @unittest.expectedFailure
    def test_will_index_new_trees(self):
        user = convenience.create_test_user()
        convenience.post_mark(user, {"#": "Hello", "@": user.email, "~": 0})
        url = convenience.get_search_api_url() + "/recall/mark/%s@%s" % (
            user.email, 0)
        response = requests.get(url)
        self.assertEquals(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()
