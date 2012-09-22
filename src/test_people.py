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
import re

from pymongo import Connection
import requests

import convenience

settings = convenience.settings

class PeopleApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        convenience.load_settings()
        self.url = "http://{host}:{port}/people/".format(
            host=settings["RECALL_API_HOST"],
            port=settings["RECALL_API_PORT"])
        self.headers = {"content-type": "application/json"}

    def tearDown(self):
        convenience.wipe_mongodb()

    def _create_test_user(self):
        test_user = convenience.create_test_user()
        return test_user.pseudonym, test_user.email, test_user.password

    def test_request_invite_with_real_name(self):
        post_data = json.dumps({"firstName": "Joe", "surname": "Bloggs",
                                "email": "joe@bloggs.com"})
        response = requests.post(self.url + "joe@bloggs.com/", data=post_data,
                                 headers=self.headers)
        self.assertEquals(202, response.status_code)

    def test_request_invite_with_pseudonym(self):
        response = requests.post(
            self.url + "j@bloggs.com/",
            data=json.dumps({"pseudonym": "jb", "email": "jb@bloggs.com"}),
            headers=self.headers)
        self.assertEqual(202, response.status_code)

    def test_verify_email(self):
        post_data = json.dumps({"pseudonym": "bloggs","email": "j@bloggs.com"})
        requests.post(self.url + "j@bloggs.com/", data=post_data, headers=self.headers)

        time.sleep(0.5)
        with open(settings["RECALL_MAILFILE"], "r") as mail_file:
            contents = mail_file.read()
            email_key =  re.search(r"[a-z0-9\-]{36}", contents).group()

        key_url = self.url + "j@bloggs.com/" + email_key
        post_data = json.dumps({"email" : "j@bloggs.com", "password": "password"})
        response = requests.post(key_url, data=post_data, headers=self.headers)
        self.assertEqual(201, response.status_code)

        db = convenience.db()
        user_in_db = db.users.find_one({"email": "j@bloggs.com"})
        self.assertIn("password_hash", user_in_db)
        self.assertNotIn("password", user_in_db)
        self.assertIn("verified", user_in_db)
        self.assertNotIn("email_verified", user_in_db)

    def test_verify_email_with_wrong_email(self):
        post_data = json.dumps({"pseudonym": "bloggs","email": "j@bloggs.com"})
        requests.post(self.url + "j@bloggs.com/", data=post_data, headers=self.headers)

        with open(settings["RECALL_MAILFILE"], "r") as mail_file:
            contents = mail_file.read()
            email_key = re.search("([0-9\-a-z]){36}", contents).group()
        # email_key = db.users.find_one()["email_key"]

        key_url = self.url + "j@bloggs.com/" + email_key
        post_data = json.dumps({"email" : "wrong email", "password": "password"})
        response = requests.post(key_url, data=post_data, headers=self.headers)
        response_data = json.loads(response.content)
        self.assertEqual(404, response.status_code)
        self.assertEqual(response_data, {
                "human_readable": "No such email_key or wrong email"})

        db = convenience.db()
        user_in_db = db.users.find_one({"email": "j@bloggs.com"})
        self.assertNotIn("password_hash", user_in_db)
        self.assertNotIn("password", user_in_db)

    def test_verify_email_with_wrong_key(self):
        post_data = json.dumps({"pseudonym": "bloggs","email": "j@bloggs.com"})
        requests.post(self.url + "j@bloggs.com/", data=post_data, headers=self.headers)

        email_key = "blah, blah, blah"

        key_url = self.url + "j@bloggs.com/" + email_key
        post_data = json.dumps({"email" : "j@bloggs.com", "password": "password"})
        response = requests.post(key_url, data=post_data, headers=self.headers)
        response_data = json.loads(response.content)
        self.assertEqual(404, response.status_code)
        self.assertEqual(response_data, {
                "human_readable": "No such email_key or wrong email"})

        db = convenience.db()
        user_in_db = db.users.find_one({"email": "j@bloggs.com"})
        self.assertNotIn("password_hash", user_in_db)
        self.assertNotIn("password", user_in_db)

    def test_verify_email_without_requesting_invite_first(self):
        post_data = json.dumps({"pseudonym": "bloggs","email": "j@bloggs.com"})
        requests.post(self.url + "j@bloggs.com/", data=post_data, headers=self.headers)

        email_key = "blah, blah, blah"

        key_url = self.url + "j@bloggs.com/" + email_key
        post_data = json.dumps({"email" : "j@bloggs.com", "password": "password"})
        response = requests.post(key_url, data=post_data, headers=self.headers)
        response_data = json.loads(response.content)
        self.assertEqual(404, response.status_code)
        self.assertEqual(response_data, {
                "human_readable": "No such email_key or wrong email"})

        db = convenience.db()
        user_in_db = db.users.find_one({"email": "j@bloggs.com"})
        self.assertNotIn("password_hash", user_in_db)
        self.assertNotIn("password", user_in_db)

    def test_verify_email_second_time(self):
        post_data = json.dumps({"pseudonym": "bloggs","email": "j@bloggs.com"})
        requests.post(self.url + "j@bloggs.com/", data=post_data, headers=self.headers)

        db = convenience.db()
        email_key = db.users.find_one()["email_key"]

        key_url = self.url + "j@bloggs.com/" + email_key
        post_data = json.dumps({"email" : "j@bloggs.com", "password": "password"})
        response = requests.post(key_url, data=post_data, headers=self.headers)
        self.assertEqual(201, response.status_code)

        user_in_db = db.users.find_one({"email": "j@bloggs.com"})
        original_password_hash = user_in_db["password_hash"]

        post_data = json.dumps({"email" : "j@bloggs.com", "password": "password"})
        response = requests.post(key_url, data=post_data, headers=self.headers)
        response_data = json.loads(response.content)

        self.assertEqual(403, response.status_code)
        self.assertEqual({"human_readable": "Already verified"}, response_data)
        user_in_db = db.users.find_one({"email": "j@bloggs.com"})
        self.assertEqual(original_password_hash, user_in_db["password_hash"])

    def test_can_check_existance_of_user(self):
        user = convenience.create_test_user()
        response = requests.get(self.url + user.email + "/")
        self.assertEquals(200, response.status_code)
        self.assertEquals(response.json.keys(), ["email"])

    def test_can_check_authentication(self):
        user = convenience.create_test_user()
        user_headers = {"X-Email": user.email, "X-Password": user.password}
        user_headers.update(self.headers)
        response = requests.get(
            self.url + user.email + "/self", headers=user_headers)
        self.assertEquals(200, response.status_code)

    def test_non_existent_user_gives_404(self):
        response = requests.get(self.url + "god/")
        self.assertEquals(404, response.status_code)
        self.assertEqual({"human_readable": "User not found"}, response.json)

if __name__ == "__main__":
    unittest.main()
