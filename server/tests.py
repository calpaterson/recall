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
import json
import time

import mock
import bcrypt
from pymongo import Connection
from werkzeug.datastructures import Headers

import server

class ServerTests(unittest.TestCase):

    def setUp(self):
        server.app.testing = True
        self.client = server.app.test_client()
        server.load_settings()
        server.settings["RECALL_MONGODB_DB_NAME"] = "test"
        server.settings["RECALL_API_HOSTNAME"] = "localhost"
        server.settings["RECALL_PASSWORD_SALT"] = bcrypt.gensalt(0)
        self.example_user_counter = 1

    def tearDown(self):
        self.db = server.get_db()
        self.db.marks.remove()
        self.db.users.remove()

    def _create_test_user(self):
        pseudonym = "example" + str(self.example_user_counter)
        email = pseudonym + "@example.com"
        password = email
        post_data = json.dumps({"pseudonym": pseudonym, "email": email})
        response = self.client.post("/user", data=str(post_data))
        assert response.status_code == 202
        self.example_user_counter += 1

        db = server.get_db()
        email_key = db.users.find_one({"email": email})["email_key"]

        post_data = json.dumps({"%password": password})
        url = "/user/" + email_key
        response = self.client.post(url, data=post_data)
        assert response.status_code == 201
        return pseudonym, email, password

    def test_request_invite_with_real_name(self):
        expected_status_code = 202
        url = "/user"
        post_data = json.dumps({"firstName": "Joe", "surname": "Bloggs",
                                "email": "joe@bloggs.com"})
        response = self.client.post(url, data=post_data)
        self.assertEquals(expected_status_code, response.status_code)

    def test_request_invite_with_pseudonym(self):
        expected_status_code = 202
        url = "/user"
        post_data = json.dumps({"pseudonym": "jb", "email": "jb@bloggs.com"})
        response = self.client.post(url, data=post_data)
        self.assertEqual(expected_status_code, response.status_code)

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

    def test_addition_of_public_mark_fails_without_password(self):
        mark = {
            "~": 0,
            "@": "example@example.com",
            "#": "Hello!"
            }
        response = self.client.post("/mark", data=str(json.dumps(mark)))
        self.assertEqual(response.status_code, 400)

        expected_data = {"error": "You must include authentication headers"}
        self.assertEqual(json.loads(response.data), expected_data)

    def test_add_and_get_public_mark(self):
        _, email, password = self._create_test_user()
        headers = Headers(
            {"X-Email": email,
             "X-Password": password})
        mark = {
            "~": 0,
            "@": email,
            "#": "Hello!",
            }
        expected_mark = {
            u"#": "Hello!",
            u"@": email,
            u"%url": u"http://localhost/mark/" + email + "/0",
            u"~": 0,
            }
        response = self.client.post(
            "/mark",
            data=str(json.dumps(mark)),
            headers=headers)
        self.assertEqual(response.status_code, 201)

        actual_mark = json.loads(
            self.client.get("/mark/"+ email +"/0").data)
        self.assertEqual(expected_mark, actual_mark)

        actual_mark = json.loads(
            self.client.get("/mark/" + email).data)[0]
        self.assertEqual(expected_mark, actual_mark)

        actual_mark = json.loads(self.client.get("/mark").data)[0]
        self.assertEqual(expected_mark, actual_mark)


    def test_add_and_get_private_mark(self):
        _, email, password = self._create_test_user()
        headers = Headers(
            {"X-Email": email,
             "X-Password": password})
        mark = {
            "~": 0,
            "@": email,
            "%private": True
            }
        expected_mark = {
            u"~": 0,
            u"@": email,
            u"%url": u"http://localhost/mark/" + email + "/0",
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


    def test_get_public_marks_of_others_while_authed(self):
        _, example, example_pass = self._create_test_user()
        mark = {
            "~": 0,
            "@": example,
            "#": "Hello!",
            }
        response = self.client.post(
            "/mark",
            data=str(json.dumps(mark)),
            headers=Headers(
                {"X-Email": example,
                 "X-Password": example_pass}))
        self.assertEqual(response.status_code, 201)

        _, eg, eg_pass = self._create_test_user()
        eg_headers = Headers(
            {"X-Email": eg,
             "X-Password": eg_pass})
        expected_mark = {
            u"#": "Hello!",
            u"@": example,
            u"%url": u"http://localhost/mark/" + example + "/0",
            u"~": 0,
            }

        response = self.client.get("/mark/" + example + "/0",
                                   headers=eg_headers).data
        actual_mark = json.loads(response)
        self.assertEqual(expected_mark, actual_mark)

        actual_mark = json.loads(
            self.client.get("/mark/" + example,
                            headers=eg_headers).data)[0]
        self.assertEqual(expected_mark, actual_mark)

        actual_mark = json.loads(self.client.get(
                "/mark", headers=eg_headers).data)[0]
        self.assertEqual(expected_mark, actual_mark)

    def test_bulk_addition_of_marks(self):
        _, example, example_pass = self._create_test_user()
        marks = [
            {
                u"~": 0,
                u"@": example,
                u"#": u"Hello",
            },
            {
                u"~": 1,
                u"@": example,
                u"#": u"Hello",
                u"%private": True
            }]

        response = self.client.post(
            "/mark",
            data=str(json.dumps(marks)),
            headers=Headers({"X-Email": example, "X-Password": example_pass}))
        self.assertEqual(202, response.status_code)

        response = self.client.get(
            "/mark/" + example,
            headers=Headers({"X-Email": example, "X-Password": example_pass}))
        parsed_response = json.loads(response.data)
        for mark in parsed_response:
            del mark["%url"]
        self.assertEqual(list(reversed(marks)), parsed_response)


if __name__ == "__main__":
    unittest.main()
