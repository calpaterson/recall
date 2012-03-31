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
        url = "/user"
        post_data = json.dumps({"pseudonym": "bloggs","email": "j@bloggs.com"})
        self.client.post(url, data=post_data)

        db = server.get_db()
        email_key = db.users.find_one()["email_key"]

        url = "/user/" + email_key
        post_data = json.dumps({"%password": "password"})
        response = self.client.post(url, data=post_data)
        self.assertEqual(201, response.status_code)

        user_in_db = db.users.find_one({"email": "j@bloggs.com"})
        self.assertIn("password_hash", user_in_db)
        self.assertNotIn("password", user_in_db)


    def test_addition_of_public_mark_fails_without_password(self):
        post_data = json.dumps({"~": 0, "@": "e@example.com", "#": "Hello!"})
        response = self.client.post("/mark", data=post_data)
        self.assertEqual(response.status_code, 400)

        expected_data = {"error": "You must include authentication headers"}
        self.assertEqual(json.loads(response.data), expected_data)


    def test_create_public_mark(self):
        _, email, password = self._create_test_user()
        headers = Headers({"X-Email": email, "X-Password": password})
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
        post_data = json.dumps(mark)
        response = self.client.post("/mark", data=post_data, headers=headers)
        self.assertEqual(response.status_code, 201)

        actual_mark = json.loads(self.client.get("/mark/"+ email +"/0").data)
        self.assertEqual(expected_mark, actual_mark)

        actual_mark = json.loads(self.client.get("/mark/" + email).data)
        self.assertEqual([expected_mark], actual_mark)

        actual_mark = json.loads(self.client.get("/mark").data)
        self.assertEqual([expected_mark], actual_mark)


    # TODO: Refactor
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
        _, user1, password1 = self._create_test_user()
        user1_headers = Headers({"X-Email": user1, "X-Password": password1})

        post_data = json.dumps({"~": 0, "@": user1, "#": "Hello!"})
        response = self.client.post(
            "/mark", data=post_data, headers=user1_headers)
        self.assertEqual(response.status_code, 201)

        _, user2, password2 = self._create_test_user()
        user2_headers = Headers({"X-Email": user2, "X-Password": password2})

        expected_mark = {u"#": "Hello!", u"@": user1,
            u"%url": u"http://localhost/mark/" + user1 + "/0", u"~": 0}

        response = self.client.get(
            "/mark/" + user1 + "/0", headers=user2_headers)
        actual_mark = json.loads(response.data)
        self.assertEqual(expected_mark, actual_mark)

        response = self.client.get("/mark/" + user1, headers=user2_headers)
        actual_marks = json.loads(response.data)
        self.assertEqual([expected_mark], actual_marks)

        response = self.client.get("/mark", headers=user2_headers)
        actual_marks = json.loads(response.data)
        self.assertEqual([expected_mark], actual_marks)


    def test_bulk_addition_of_marks(self):
        _, example, example_pass = self._create_test_user()
        headers = Headers({"X-Email": example,
                           "X-Password": example_pass})

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

        url = "/mark"
        post_data = json.dumps(marks)
        response = self.client.post(url, data=post_data, headers=headers)
        self.assertEqual(202, response.status_code)

        expected_response_data = list(reversed(marks))
        response = self.client.get("/mark/" + example, headers=headers)
        actual_response_data = json.loads(response.data)
        for mark in actual_response_data:
            del mark["%url"]
        self.assertEqual(actual_response_data, actual_response_data)


if __name__ == "__main__":
    unittest.main()
