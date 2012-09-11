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

from pymongo import Connection
from werkzeug.datastructures import Headers
import requests

import convenience
import server

settings = convenience.settings

class ServerTests(unittest.TestCase):
    def setUp(self):
        self.client = server.oldapp.test_client()
        convenience.load_settings()

    def tearDown(self):
        convenience.wipe_mongodb()

    def _base_url(self):
        return convenience.api_url()

    def _create_test_user(self):
        test_user = convenience.create_test_user()
        return test_user.pseudonym, test_user.email, test_user.password

    def test_request_invite_with_real_name(self):
        expected_status_code = 202
        url = self._base_url() + "/user"
        post_data = json.dumps({"firstName": "Joe", "surname": "Bloggs",
                                "email": "joe@bloggs.com"})
        response = requests.post(url, data=post_data)
        self.assertEquals(expected_status_code, response.status_code)

    def test_request_invite_with_pseudonym(self):
        response = requests.post(self._base_url() + "/user", data=json.dumps(
                {"pseudonym": "jb", "email": "jb@bloggs.com"}))
        self.assertEqual(202, response.status_code)

    def test_verify_email(self):
        url = self._base_url() + "/user"
        post_data = json.dumps({"pseudonym": "bloggs","email": "j@bloggs.com"})
        requests.post(url, data=post_data)

        db = convenience.db()
        email_key = db.users.find_one()["email_key"]

        url = self._base_url() +  "/user/" + email_key
        post_data = json.dumps({"email" : "j@bloggs.com", "password": "password"})
        response = requests.post(url, data=post_data)
        self.assertEqual(201, response.status_code)

        user_in_db = db.users.find_one({"email": "j@bloggs.com"})
        self.assertIn("password_hash", user_in_db)
        self.assertNotIn("password", user_in_db)
        self.assertIn("verified", user_in_db)
        self.assertNotIn("email_verified", user_in_db)

    def test_verify_email_with_wrong_email(self):
        url = self._base_url() + "/user"
        post_data = json.dumps({"pseudonym": "bloggs","email": "j@bloggs.com"})
        requests.post(url, data=post_data)

        db = convenience.db()
        email_key = db.users.find_one()["email_key"]

        url = self._base_url() + "/user/" + email_key
        post_data = json.dumps({"email" : "wrong email", "password": "password"})
        response = requests.post(url, data=post_data)
        response_data = json.loads(response.content)
        self.assertEqual(404, response.status_code)
        self.assertEqual(response_data, {
                "human_readable": "No such email_key or wrong email"})

        user_in_db = db.users.find_one({"email": "j@bloggs.com"})
        self.assertNotIn("password_hash", user_in_db)
        self.assertNotIn("password", user_in_db)

    def test_verify_email_with_wrong_key(self):
        url =  self._base_url() + "/user"
        post_data = json.dumps({"pseudonym": "bloggs","email": "j@bloggs.com"})
        requests.post(url, data=post_data)

        email_key = "blah, blah, blah"

        url = self._base_url() + "/user/" + email_key
        post_data = json.dumps({"email" : "j@bloggs.com", "password": "password"})
        response = requests.post(url, data=post_data)
        response_data = json.loads(response.content)
        self.assertEqual(404, response.status_code)
        self.assertEqual(response_data, {
                "human_readable": "No such email_key or wrong email"})

        db = convenience.db()
        user_in_db = db.users.find_one({"email": "j@bloggs.com"})
        self.assertNotIn("password_hash", user_in_db)
        self.assertNotIn("password", user_in_db)

    def test_verify_email_without_requesting_invite_first(self):
        url = self._base_url() + "/user"
        post_data = json.dumps({"pseudonym": "bloggs","email": "j@bloggs.com"})
        requests.post(url, data=post_data)

        email_key = "blah, blah, blah"

        url = self._base_url() + "/user/" + email_key
        post_data = json.dumps({"email" : "j@bloggs.com", "password": "password"})
        response = requests.post(url, data=post_data)
        response_data = json.loads(response.content)
        self.assertEqual(404, response.status_code)
        self.assertEqual(response_data, {
                "human_readable": "No such email_key or wrong email"})

        db = convenience.db()
        user_in_db = db.users.find_one({"email": "j@bloggs.com"})
        self.assertNotIn("password_hash", user_in_db)
        self.assertNotIn("password", user_in_db)

    def test_verify_email_second_time(self):
        url = self._base_url() + "/user"
        post_data = json.dumps({"pseudonym": "bloggs","email": "j@bloggs.com"})
        requests.post(url, data=post_data)

        db = convenience.db()
        email_key = db.users.find_one()["email_key"]

        url = self._base_url() + "/user/" + email_key
        post_data = json.dumps({"email" : "j@bloggs.com", "password": "password"})
        response = requests.post(url, data=post_data)
        self.assertEqual(201, response.status_code)

        user_in_db = db.users.find_one({"email": "j@bloggs.com"})
        original_password_hash = user_in_db["password_hash"]

        url = self._base_url() +  "/user/" + email_key
        post_data = json.dumps({"email" : "j@bloggs.com", "password": "password"})
        response = requests.post(url, data=post_data)
        response_data = json.loads(response.content)

        self.assertEqual(403, response.status_code)
        self.assertEqual({"human_readable": "Already verified"}, response_data)
        user_in_db = db.users.find_one({"email": "j@bloggs.com"})
        self.assertEqual(original_password_hash, user_in_db["password_hash"])


    def test_addition_of_public_mark_fails_without_password(self):
        url = self._base_url() + "/mark"
        post_data = json.dumps({"~": 0, "@": "e@example.com", "#": "Hello!"})
        response = requests.post(url, data=post_data)
        self.assertEqual(response.status_code, 400)

        expected_data = {"human_readable": "You must include authentication headers"}
        self.assertEqual(json.loads(response.content), expected_data)


    def test_create_public_mark(self):
        user = convenience.create_test_user()
        mark = {"~": 0, "@": user.email, "#": "Hello!"}

        post_response = requests.post(
            self._base_url() + "/mark", data=json.dumps(mark),
            headers=user.headers())
        mark_directly = json.loads(
            requests.get("{base_url}/mark/{email}/0".format(
                    base_url=self._base_url(), email=user.email)).content)
        mark_from_users_marks = json.loads(
            requests.get("{base_url}/mark/{email}".format(
                    base_url=self._base_url(), email=user.email)).content)
        mark_from_all_marks = json.loads(
            requests.get(self._base_url() + "/mark").content)

        self.assertEqual(post_response.status_code, 202)
        convenience.assert_marks_equal(mark, mark_directly)
        convenience.assert_marks_equal(mark, mark_from_users_marks[0])
        convenience.assert_marks_equal(mark, mark_from_all_marks[0])


    def test_add_and_get_private_mark(self):
        _, email, password = self._create_test_user()
        headers = Headers({"X-Email": email, "X-Password": password})
        mark = {"~": 0, "@": email, "%private": True, "#": "Hello"}
        expected_mark = {
            u"~": 0,
            u"#": "Hello",
            u"@": email,
            u"%url": settings["RECALL_API_BASE_URL"] + u"/mark/" + email + "/0",
            u"%private": True,
            u"£created": 0
            }

        url = self._base_url() + "/mark"
        post_data = json.dumps(mark)
        response = requests.post(url, headers=headers, data=post_data)
        self.assertEqual(response.status_code, 202)

        public_marks = json.loads(requests.get(url).content)
        self.assertEqual([], public_marks)

        email_marks = json.loads(
            requests.get(url, headers=headers).content)
        convenience.assert_marks_equal([expected_mark], email_marks)

        public_email_marks = json.loads(requests.get(url + "/" + email).content)
        convenience.assert_marks_equal([], public_email_marks)

        private_email_marks = json.loads(
            requests.get(url + "/" + email, headers=headers).content)
        convenience.assert_marks_equal([expected_mark], private_email_marks)

        specific_mark_response = requests.get(url + "/" + email + "/0")
        self.assertEqual(404, specific_mark_response.status_code)

        specific_mark_with_auth = json.loads(
            requests.get(url + "/" + email + "/0", headers=headers).content)
        convenience.assert_marks_equal(expected_mark, specific_mark_with_auth)


    def test_cannot_create_public_mark_without_who_and_when(self):
        _, email, password = self._create_test_user()
        headers = Headers({"X-Email": email, "X-Password": password})
        mark1 = {"~": 0, "#": "Hello"}
        mark2 = {"@": email, "#": "Hello"}

        expected_response_data = {
            "human_readable": "Must include @ and ~ with all marks"}

        url = self._base_url() + "/mark"
        post_data = json.dumps(mark1)
        response = requests.post(url, headers=headers, data=post_data)
        response_data = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_data, expected_response_data)

        post_data = json.dumps(mark2)
        response = requests.post(url, headers=headers, data=post_data)
        response_data = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_data, expected_response_data)


    def test_get_public_marks_of_others_while_authed(self):
        _, user1, password1 = self._create_test_user()
        user1_headers = Headers({"X-Email": user1, "X-Password": password1})

        post_data = json.dumps({"~": 0, "@": user1, "#": "Hello!"})
        response = requests.post(
            self._base_url() + "/mark", data=post_data, headers=user1_headers)
        self.assertEqual(response.status_code, 202)

        _, user2, password2 = self._create_test_user()
        user2_headers = Headers({"X-Email": user2, "X-Password": password2})

        expected_mark = {u"#": "Hello!", u"@": user1,
                         u"%url": settings["RECALL_API_BASE_URL"] + u"/mark/" + user1 + "/0",
                         u"~": 0, u"£created": 0}

        response = requests.get(
            self._base_url() + "/mark/" + user1 + "/0", headers=user2_headers)
        actual_mark = json.loads(response.content)
        convenience.assert_marks_equal(expected_mark, actual_mark)

        response = requests.get(self._base_url() + "/mark/" + user1, headers=user2_headers)
        actual_marks = json.loads(response.content)
        convenience.assert_marks_equal([expected_mark], actual_marks)

        response = requests.get(self._base_url() + "/mark", headers=user2_headers)
        actual_marks = json.loads(response.content)
        convenience.assert_marks_equal([expected_mark], actual_marks)


    def test_bulk_addition_of_marks(self):
        user = convenience.create_test_user()
        marks = [
            {
                u"~": 0,
                u"@": user.email,
                u"#": u"Hello",
            },
            {
                u"~": 1,
                u"@": user.email,
                u"#": u"Hello",
                u"%private": True
            }]

        post_response = requests.post(
            self._base_url() + "/mark", data=json.dumps(marks),
            headers=user.headers())
        get_response = requests.get(self._base_url() + "/mark/" + user.email,
                                   headers=user.headers())

        actual_response_data = json.loads(get_response.content)
        for mark in actual_response_data:
            del mark["%url"]
            del mark[u"£created"]
        expected_response_data = list(reversed(marks))
        self.assertEqual(202, post_response.status_code)
        self.assertEqual(expected_response_data, actual_response_data)


    def test_marks_with_reserved_keys_refused(self):
        def assertError(expected_response_data, mark):
            url = self._base_url() + "/mark"
            post_data = json.dumps(mark)
            response = requests.post(url, data=post_data, headers=headers)
            response_data = json.loads(response.content)
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


## BAD TESTS (2)


    def test_trying_to_get_many_marks_at_once_is_refused(self):
        expected_mark_limit = settings["RECALL_MARK_LIMIT"] = 2
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


## END BAD TESTS


    def test_get_marks_since(self):
        _, email, password = self._create_test_user()
        headers = Headers({"X-Email": email, "X-Password": password})
        marks = []
        for time in xrange(0, 5):
            marks.append({"@": email, "~": time})
        url = self._base_url() + "/mark"
        post_data = json.dumps(marks)
        requests.post(url, data=post_data, headers=headers)

        url = self._base_url() + "/mark?since=1"
        response = requests.get(url, headers=headers)
        response_data = json.loads(response.content)
        self.assertEqual(200, response.status_code)
        mark_times = map(lambda mark: mark["~"], response_data)
        self.assertEqual([4, 3, 2], mark_times)

        url = self._base_url() + "/mark/%s?since=1" % email
        response = requests.get(url, headers=headers)
        response_data = json.loads(response.content)
        self.assertEqual(200, response.status_code)
        mark_times = map(lambda mark: mark["~"], response_data)
        self.assertEqual([4, 3, 2], mark_times)


    def test_get_marks_before(self):
        _, email, password = self._create_test_user()
        headers = Headers({"X-Email": email, "X-Password": password})
        marks = []
        for time in xrange(0, 5):
            marks.append({"@": email, "~": time})
        url = self._base_url() + "/mark"
        post_data = json.dumps(marks)
        requests.post(url, data=post_data, headers=headers)

        url = self._base_url() + "/mark?before=3"
        response = requests.get(url, headers=headers)
        response_data = json.loads(response.content)
        self.assertEqual(200, response.status_code)
        mark_times = map(lambda mark: mark["~"], response_data)
        self.assertEqual([2, 1, 0], mark_times)

        url = self._base_url() + "/mark/%s?before=3" % email
        response = requests.get(url, headers=headers)
        response_data = json.loads(response.content)
        self.assertEqual(200, response.status_code)
        mark_times = map(lambda mark: mark["~"], response_data)
        self.assertEqual([2, 1, 0], mark_times)


    def test_can_check_existance_of_user(self):
        user = convenience.create_test_user()
        response = requests.get(self._base_url() + "/user/" + user.email)
        self.assertEquals(200, response.status_code)
        self.assertNotIn("self", json.loads(response.content))

    def test_can_check_authentication(self):
        user = convenience.create_test_user()
        response = requests.get(self._base_url() + "/user/" + user.email,
                                headers=user.headers())
        self.assertEquals(200, response.status_code)
        self.assertIn("self", json.loads(response.content))

    def test_non_existent_user_gives_404(self):
        response = requests.get(self._base_url() + "/user/god")
        self.assertEquals(404, response.status_code)
        self.assertEqual(None, json.loads(response.content))

    def test_error_handler_always_returns_json_object(self):
        try:
            raise Exception
        except Exception as e:
            data, status = server.handle_exception(e)
            self.assertIn("human_readable", json.loads(data))
