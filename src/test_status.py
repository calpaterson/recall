#!/usr/bin/env python
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

import unittest

import requests

from recall import convenience as conv

settings = conv.settings

class StatusTests(unittest.TestCase):
    def test_status(self):
        # When
        response = requests.get(
            "http://{host}:{port}/status".format(
                host=settings["RECALL_API_HOST"],
                port=settings["RECALL_API_PORT"]))
        # Then
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {
                "job_queue": "ok",
                "search": "ok"})

if __name__ == '__main__':
    unittest.main()
