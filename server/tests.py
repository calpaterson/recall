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
        server.settings["RECALL_API_BASE_URL"] = "http://test"
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

        post_data = json.dumps({"password": password, "email": email})
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
        post_data = json.dumps({"email" : "j@bloggs.com", "password": "password"})
        response = self.client.post(url, data=post_data)
        self.assertEqual(201, response.status_code)

        user_in_db = db.users.find_one({"email": "j@bloggs.com"})
        self.assertIn("password_hash", user_in_db)
        self.assertNotIn("password", user_in_db)

    def test_verify_email_with_wrong_email(self):
        url = "/user"
        post_data = json.dumps({"pseudonym": "bloggs","email": "j@bloggs.com"})
        self.client.post(url, data=post_data)

        db = server.get_db()
        email_key = db.users.find_one()["email_key"]

        url = "/user/" + email_key
        post_data = json.dumps({"email" : "wrong email", "password": "password"})
        response = self.client.post(url, data=post_data)
        response_data = json.loads(response.data)
        self.assertEqual(404, response.status_code)
        self.assertEqual(response_data, {
                "human_readable": "No such email_key or wrong email"})

        user_in_db = db.users.find_one({"email": "j@bloggs.com"})
        self.assertNotIn("password_hash", user_in_db)
        self.assertNotIn("password", user_in_db)

    @unittest.expectedFailure
    def test_verify_email_with_wrong_key(self):
        url = "/user"
        post_data = json.dumps({"pseudonym": "bloggs","email": "j@bloggs.com"})
        self.client.post(url, data=post_data)

        email_key = "blah, blah, blah"

        url = "/user/" + email_key
        post_data = json.dumps({"email" : "j@bloggs.com", "password": "password"})
        response = self.client.post(url, data=post_data)
        response_data = json.loads(response.data)
        self.assertEqual(404, response.status_code)
        self.assertEqual(response_data, {
                "human_readable": "No such email_key or wrong email"})

        user_in_db = db.users.find_one({"email": "j@bloggs.com"})
        self.assertNotIn("password_hash", user_in_db)
        self.assertNotIn("password", user_in_db)

    @unittest.expectedFailure
    def test_verify_email_without_requesting_invite_first(self):
        email_key = "blah, blah, blah"

        url = "/user/" + email_key
        post_data = json.dumps({"email" : "j@bloggs.com", "password": "password"})
        response = self.client.post(url, data=post_data)
        self.assertEqual(404, response.status_code)
        self.assertEqual(response_data, {
                "human_readable": "No such email_key or wrong email"})


        user_in_db = db.users.find_one({"email": "j@bloggs.com"})
        self.assertNotIn("password_hash", user_in_db)
        self.assertNotIn("password", user_in_db)

    @unittest.expectedFailure
    def test_verify_email_second_time(self):
        url = "/user"
        post_data = json.dumps({"pseudonym": "bloggs","email": "j@bloggs.com"})
        self.client.post(url, data=post_data)

        db = server.get_db()
        email_key = db.users.find_one()["email_key"]

        url = "/user/" + email_key
        post_data = json.dumps({"email" : "j@bloggs.com", "password": "password"})
        response = self.client.post(url, data=post_data)
        self.assertEqual(201, response.status_code)

        user_in_db = db.users.find_one({"email": "j@bloggs.com"})
        original_password_hash = user_in_db["password_hash"]

        url = "/user/" + email_key
        post_data = json.dumps({"email" : "j@bloggs.com", "password": "password"})
        response = self.client.post(url, data=post_data)
        response_data = json.loads(response.data)

        self.assertEqual(403, response.status_code)
        self.assertEqual({"human_readable": "Already verified"})
        user_in_db = db.users.find_one({"email": "j@bloggs.com"})
        self.assertEqual(original_password_hash, user_in_db["password_hash"])


    def test_addition_of_public_mark_fails_without_password(self):
        post_data = json.dumps({"~": 0, "@": "e@example.com", "#": "Hello!"})
        response = self.client.post("/mark", data=post_data)
        self.assertEqual(response.status_code, 400)

        expected_data = {"human_readable": "You must include authentication headers"}
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
            u"%url": u"http://test/mark/" + email + "/0",
            u"~": 0,
            u"£created": 0
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


    def test_add_and_get_private_mark(self):
        _, email, password = self._create_test_user()
        headers = Headers({"X-Email": email, "X-Password": password})
        mark = {"~": 0, "@": email, "%private": True, "#": "Hello"}
        expected_mark = {
            u"~": 0,
            u"#": "Hello",
            u"@": email,
            u"%url": u"http://test/mark/" + email + "/0",
            u"%private": True,
            u"£created": 0
            }

        url = "/mark"
        post_data = json.dumps(mark)
        response = self.client.post(url, headers=headers, data=post_data)
        self.assertEqual(response.status_code, 201)

        public_marks = json.loads(self.client.get("/mark").data)
        self.assertEqual([], public_marks)

        email_marks = json.loads(
            self.client.get("/mark", headers=headers).data)
        self.assertEqual([expected_mark], email_marks)

        public_email_marks = json.loads(self.client.get("/mark/" + email).data)
        self.assertEqual([], public_email_marks)

        private_email_marks = json.loads(
            self.client.get("/mark/" + email, headers=headers).data)
        self.assertEqual([expected_mark], private_email_marks)

        specific_mark_response = self.client.get("/mark/" + email + "/0")
        self.assertEqual(404, specific_mark_response.status_code)

        specific_mark_with_auth = json.loads(
            self.client.get("/mark/" + email + "/0", headers=headers).data)
        self.assertEqual(expected_mark, specific_mark_with_auth)


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
                         u"%url": u"http://test/mark/" + user1 + "/0",
                         u"~": 0, u"£created": 0}

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
            del mark[u"£created"]
        self.assertEqual(expected_response_data, actual_response_data)


    def test_marks_with_reserved_keys_refused(self):
        def assertError(expected_response_data, mark):
            url = "/mark"
            post_data = json.dumps(mark)
            response = self.client.post(url, data=post_data, headers=headers)
            response_data = json.loads(response.data)
            self.assertEqual(400, response.status_code, msg=post_data)
            self.assertEqual(expected_response_data, response_data)

        _, email, password = self._create_test_user()
        headers = Headers({"X-Email": email, "X-Password": password})

        problematic_marks = [
            {"~": 0, "@": email, "$problem": True},
            {"~": 0, "@": email, "submap": {"$problem": True}},
            {"~": 0, "@": email, u"£problem": True},
            ]
        expected_response_dollar = {
                u"human_readable": u"Mark keys may not be prefixed with $ or £",
                u"machine_readable": u"$problem"}
        expected_response_pound = {
                u"human_readable": u"Mark keys may not be prefixed with $ or £",
                u"machine_readable": u"£problem"}
        assertError(expected_response_dollar, problematic_marks[0])
        assertError(expected_response_dollar, problematic_marks[1])
        assertError(expected_response_pound, problematic_marks[2])


    def test_trying_to_get_many_marks_at_once_is_refused(self):
        expected_mark_limit = server.settings["RECALL_MARK_LIMIT"] = 2
        _, email, password = self._create_test_user()
        headers = Headers({"X-Email": email, "X-Password": password})
        marks = []
        for time in xrange(0, expected_mark_limit + 1):
            marks.append({"@": email, "~": time})
        url = "/mark"
        post_data = json.dumps(marks)
        self.client.post(url, data=post_data, headers=headers)

        response = self.client.get(url, headers=headers)
        response_data = json.loads(response.data)
        expected_response_data = {
            u"human_readable": u"May not request more than %s marks at once" %
            expected_mark_limit,
            "machine_readable": expected_mark_limit}
        self.assertEqual(413, response.status_code)
        self.assertEqual(expected_response_data, response_data)

        url = "/mark/%s" % email
        response = self.client.get(url, headers=headers)
        response_data = json.loads(response.data)
        self.assertEqual(413, response.status_code)
        self.assertEqual(expected_response_data, response_data)


    def test_get_limited_number_of_marks(self):
        _, email, password = self._create_test_user()
        headers = Headers({"X-Email": email, "X-Password": password})
        marks = []
        for time in xrange(0, 5):
            marks.append({"@": email, "~": time})
        url = "/mark"
        post_data = json.dumps(marks)
        self.client.post(url, data=post_data, headers=headers)

        url = "/mark?maximum=2"
        response = self.client.get(url, headers=headers)
        response_data = json.loads(response.data)
        self.assertEqual(200, response.status_code)
        mark_times = map(lambda mark: mark["~"], response_data)
        self.assertEqual([4, 3], mark_times)

        url = "/mark/%s?maximum=2" % email
        response = self.client.get(url, headers=headers)
        response_data = json.loads(response.data)
        self.assertEqual(200, response.status_code)
        mark_times = map(lambda mark: mark["~"], response_data)
        self.assertEqual([4, 3], mark_times)

    def test_get_marks_since(self):
        _, email, password = self._create_test_user()
        headers = Headers({"X-Email": email, "X-Password": password})
        marks = []
        for time in xrange(0, 5):
            marks.append({"@": email, "~": time})
        url = "/mark"
        post_data = json.dumps(marks)
        self.client.post(url, data=post_data, headers=headers)

        url = "/mark?since=1"
        response = self.client.get(url, headers=headers)
        response_data = json.loads(response.data)
        self.assertEqual(200, response.status_code)
        mark_times = map(lambda mark: mark["~"], response_data)
        self.assertEqual([4, 3, 2], mark_times)

        url = "/mark/%s?since=1" % email
        response = self.client.get(url, headers=headers)
        response_data = json.loads(response.data)
        self.assertEqual(200, response.status_code)
        mark_times = map(lambda mark: mark["~"], response_data)
        self.assertEqual([4, 3, 2], mark_times)


    def test_get_marks_before(self):
        _, email, password = self._create_test_user()
        headers = Headers({"X-Email": email, "X-Password": password})
        marks = []
        for time in xrange(0, 5):
            marks.append({"@": email, "~": time})
        url = "/mark"
        post_data = json.dumps(marks)
        self.client.post(url, data=post_data, headers=headers)

        url = "/mark?before=3"
        response = self.client.get(url, headers=headers)
        response_data = json.loads(response.data)
        self.assertEqual(200, response.status_code)
        mark_times = map(lambda mark: mark["~"], response_data)
        self.assertEqual([2, 1, 0], mark_times)

        url = "/mark/%s?before=3" % email
        response = self.client.get(url, headers=headers)
        response_data = json.loads(response.data)
        self.assertEqual(200, response.status_code)
        mark_times = map(lambda mark: mark["~"], response_data)
        self.assertEqual([2, 1, 0], mark_times)

    def test_user_able_to_check_authentication(self):
        _, email, password = self._create_test_user()
        headers = Headers({"X-Email": email, "X-Password": password})

        response = self.client.get("/user/%s" % email)
        response_data = json.loads(response.data)
        self.assertNotIn("self", response_data)
        self.assertEquals(200, response.status_code)

        response = self.client.get("/user/%s" % email, headers=headers)
        response_data = json.loads(response.data)
        self.assertTrue(response_data.get("self", False))


    @unittest.expectedFailure
    def test_before_and_since(self):
        self.fail()

if __name__ == "__main__":
    unittest.main()
