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
from werkzeug.datastructures import Headers

import server

class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._db = Connection()["test"]

    def setUp(self):
        server.app.testing = True
        self.client = server.app.test_client()
        server.load_settings()
        server.settings["RECALL_MONGODB_DB_NAME"] = "test"
        server.settings["RECALL_API_HOSTNAME"] = "localhost"

    def tearDown(self):
        self.db = Connection()["test"]
        self.db.marks.remove()
        self.db.users.remove()

    def add_example_user(self):
        """Adds the user example@example.com/password"""
        self.client.post(
            "/user",
            data=str(json.dumps({
                        "pseudonym": "example",
                        "email": "example@example.com"})))

        db = server.get_db()
        email_key = db.users.find_one()["email_key"]

        response = self.client.post(
            "/user/" + email_key,
            data=str(json.dumps({"%password": "password"})))

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
            data=str(json.dumps({"%password": "password"})))
        self.assertEqual(expected_status_code, response.status_code)

        self.assertNotIn("password", db.users.find_one())

        self.assertIn("password_hash", db.users.find_one())

    def test_addition_of_public_mark(self):
        self.add_example_user()
        headers = Headers(
            {"X-Email": "example@example.com",
             "X-Password": "password"})
        mark = {
            "~": 0,
            "@": "example@example.com",
            "#": "Hello!",
            }
        expected_mark = {
            u"#": "Hello!",
            u"@": u"example@example.com",
            u"url": u"http://localhost/mark/example@example.com/0",
            u"~": 0,
            }
        response = self.client.post(
            "/mark",
            data=str(json.dumps(mark)),
            headers=headers)
        self.assertEqual(response.status_code, 201)

        actual_mark = json.loads(
            self.client.get("/mark/example@example.com/0").data)
        self.assertEqual(expected_mark, actual_mark)

        actual_mark = json.loads(
            self.client.get("/mark/example@example.com").data)[0]
        self.assertEqual(
            expected_mark, actual_mark,
            msg="Contents of public mark not as expected")

        actual_mark = json.loads(self.client.get("/mark").data)[0]
        self.assertEqual(
            expected_mark, actual_mark,
            msg="Contents of public mark not as expected")

    def test_addition_of_public_mark_fails_without_password(self):
        mark = {
            "~": 0,
            "@": "example@example.com",
            "#": "Hello!"
            }
        response = self.client.post("/mark", data=str(json.dumps(mark)))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, "You must include a %password")


    def test_addition_of_private_mark(self):
        self.add_example_user()
        headers = Headers(
            {"X-Email": "example@example.com",
             "X-Password": "password"})
        mark = {
            "~": 0,
            "@": "example@example.com",
            "%private": True
            }
        expected_mark = {
            u"~": 0,
            u"@": u"example@example.com",
            u"url": u"http://localhost/mark/example@example.com/0",
            u"%private": True
            }

        response = self.client.post(
            "/mark",
            headers=headers,
            data=str(json.dumps(mark)))
        self.assertEqual(response.status_code, 201)

        marks = json.loads(self.client.get("/mark").data)
        self.assertEqual([], marks)

        marks = json.loads(self.client.get(
                "/mark",
                headers=headers).data)
        self.assertEqual([expected_mark], marks)

        marks = json.loads(self.client.get(
                "/mark/example@example.com").data)
        self.assertEqual([], marks)

        marks = json.loads(
            self.client.get(
                "/mark/example@example.com",
                headers=headers).data)
        self.assertEqual([expected_mark], marks)

        response = self.client.get("/mark/example@example.com/0")
        self.assertEqual(404, response.status_code)

        marks = json.loads(
            self.client.get(
                "/mark/example@example.com/0",
                headers=headers).data)
        self.assertEqual(expected_mark, marks)

if __name__ == "__main__":
    unittest.main()
