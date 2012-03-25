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
import json

import mock
from pymongo import Connection

import server

class ServerTests(unittest.TestCase):
    def setUp(self):
        self.client = server.app.test_client()
        server.settings["IS_TEST"] = True
        server.load_settings()
        server.settings["RECALL_MONGODB_DB_NAME"] = "test"

    def tearDown(self):
        db = Connection()["test"]
        db.marks.remove()
        db.users.remove()

    def test_request_invite_with_real_name(self):
        expected_status_code = 202
        response = self.client.post(
            "/user",
            data=str(json.dumps({
                        "firstName": "joe",
                        "surname": "bloggs",
                        "email": "joe@bloggs.com"})))
        self.assertEquals(expected_status_code, response.status_code,
                          msg=response.data)

    def test_request_invite_with_pseudonym(self):
        expected_status_code = 202
        response = self.client.post(
            "/user",
            data=str(json.dumps({
                        "pseudonym": "bloggs",
                        "email": "joe@bloggs.com"})))
        self.assertEqual(expected_status_code, response.status_code,
                         msg=response.data)

    def test_verify_email(self):
        self.client.post(
            "/user",
            data=str(json.dumps({
                        "pseudonym": "bloggs",
                        "email": "joe@bloggs.com"})))

        db = server.get_db()
        email_key = db.users.find_one()["email_key"]

        expected_status_code = 201
        response = self.client.post(
            "/user/" + email_key,
            data=str(json.dumps({"password": "password"})))
        self.assertEqual(expected_status_code, response.status_code)

        self.assertNotIn("password", db.users.find_one())

        self.assertIn("password_hash", db.users.find_one())

if __name__ == "__main__":
    unittest.main()
