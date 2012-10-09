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

from __future__ import absolute_import

from urllib import quote
import unittest
import json
import time
import os.path

from pymongo import Connection
import requests

from recall import convenience as conv
from recall import search

settings = conv.settings

class BookmarkApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        conv.load_settings()
        cls.url = "http://{host}:{port}/bookmarks/".format(
            host=settings["RECALL_API_HOST"],
            port=settings["RECALL_API_PORT"])

    # def setUp(self):
    #     search.set_mapping()

    def tearDown(self):
        conv.wipe_mongodb()
        search.clear()

    def _create_test_user(self):
        test_user = conv.create_test_user()
        return test_user.pseudonym, test_user.email, test_user.password

    def headers(self, user=None):
        basic = {"content-type": "application/json"}
        if user is not None:
            basic.update(user.headers())
        return basic

    def test_addition_of_public_mark_fails_without_password(self):
        response = requests.post(
            self.url + "e@example.com/public/0/",
            data=json.dumps({"~": 0, "@": "e@example.com", "#": "Hello!"}),
            headers=self.headers())
        self.assertEqual(response.status_code, 400)

        expected_data = {"human_readable": "You must include authenticate"}
        self.assertEqual(json.loads(response.content), expected_data)

    def test_add_public_bookmark(self):
        user = conv.create_test_user()
        add_response = requests.post(
            self.url + user.email + "/public/0/",
            data=json.dumps({"~": 0, "@": user.email, "#": "Hello!"}),
            headers=self.headers(user))
        self.assertEqual(add_response.status_code, 202)
        def inner():
            get_response = requests.get(self.url + "public/?q=hello")
            self.assertEqual(get_response.status_code, 200)
        conv.with_patience(inner)

    def test_add_private_bookmark(self):
        user = conv.create_test_user()
        add_response = requests.post(
            self.url + user.email + "/private/0/",
            data=json.dumps({"~": 0, "@": user.email, "#": "Hello!"}),
            headers=self.headers(user))
        self.assertEqual(add_response.status_code, 202)
        def inner():
            all_response = requests.get(
                self.url + user.email + "/all/?q=hello",
                headers=user.headers())
            self.assertEqual(all_response.status_code, 200)
            public_response = requests.get(self.url + "public/?q=hello")
            self.assertEqual(public_response.status_code, 404)
        conv.with_patience(inner)

    def _test_import_from_filepath(self, path):
        def inner():
            all_response = requests.get(
                self.url + user.email + "/all/",
                headers=user.headers())
            self.assertEqual(all_response.status_code, 200)
        with open(path, "r") as bookmark_file:
            contents = bookmark_file.read()
            user = conv.create_test_user()
            headers = user.headers()
            headers.update({"content-type": "text/html"})
            import_response = requests.patch(
                self.url + user.email + "/",
                data=contents,
                headers=headers)
        self.assertEqual(import_response.status_code, 202)
        conv.with_patience(inner)

    def test_import_from_firefox(self):
        bookmark_file_path = os.path.abspath(
            os.path.dirname(__file__) +
            "/../ops/data/firefox-bookmarks.html")
        self._test_import_from_filepath(bookmark_file_path)

    def test_import_from_chrome(self):
        bookmark_file_path = os.path.abspath(
            os.path.dirname(__file__) +
            "/../ops/data/chrome-bookmarks.html")
        self._test_import_from_filepath(bookmark_file_path)

    def test_import_from_pinboard(self):
        bookmark_file_path = os.path.abspath(
            os.path.dirname(__file__) +
            "/../ops/data/pinboard-bookmarks.html")
        self._test_import_from_filepath(bookmark_file_path)

    def test_recent_bookmarks(self):
        # Given
        user2 = conv.create_test_user()
        headers = user2.headers()
        headers.update({"content-type": "application/json"})
        requests.post(
            self.url + user2.email + "/public/0/",
            data=json.dumps({"~": 0, "@": user2.email, "#": "World!"}),
            headers=headers)

        user = conv.create_test_user()
        headers = user.headers()
        headers.update({"content-type": "application/json"})
        requests.post(
            self.url + user.email + "/private/0/",
            data=json.dumps({"~": 0, "@": user.email, "#": "Hello!"}),
            headers=headers)
        requests.post(
            self.url + user.email + "/private/1/",
            data=json.dumps({"~": 1, "@": user.email, "#": "World!"}),
            headers=headers)
        def inner():
            # When
            response = requests.get(
                self.url + user.email + "/all/recent/",
                headers=headers)

            # Then
            self.assertEqual(200, response.status_code)
            self.assertTrue(len(response.json) == 2)
            self.assertEqual(1, response.json[0]["~"])
            self.assertEqual(0, response.json[1]["~"])
            self.assertEqual("2", response.headers["X-Recall-Total"])
        conv.with_patience(inner)

    @unittest.expectedFailure
    def test_get_bookmark_by_url(self):
        user = conv.create_test_user()
        headers = user.headers()
        headers.update({"content-type": "application/json"})
        hyperlink = "http://www.example.com/?q=1"
        requests.post(
            self.url + user.email + "/private/0/",
            data=json.dumps({"~": 0, "@": user.email,
                             "hyperlink": hyperlink}))
        url = self.url + "public/url/" + quote(hyperlink, safe="")
        def inner():
            response = requests.get(url)
            self.assertEqual(200, response.status_code)

        conv.with_patience(inner)


    # Can't create bookmark without @ and ~

    # Can get own private bookmarks

    # Can't get other's private bookmarks

    # Can't use reserved keys

    # Can search fulltext

    # Can search fulltext on old bookmarks

    # Can import

    # Can export

    # @unittest.expectedFailure
    # def test_add_and_get_private_mark(self):
    #     _, email, password = self._create_test_user()
    #     headers = {"X-Email": email, "X-Password": password}
    #     mark = {"~": 0, "@": email, "%private": True, "#": "Hello"}
    #     expected_mark = {
    #         u"~": 0,
    #         u"#": "Hello",
    #         u"@": email,
    #         u"%url": settings["RECALL_API_BASE_URL"] + u"/mark/" + email + "/0",
    #         u"%private": True,
    #         u"£created": 0
    #         }

    #     url = self._base_url() + "/mark"
    #     post_data = json.dumps(mark)
    #     response = requests.post(url, headers=headers, data=post_data)
    #     self.assertEqual(response.status_code, 202)

    #     public_marks = json.loads(requests.get(url).content)
    #     self.assertEqual([], public_marks)

    #     email_marks = json.loads(
    #         requests.get(url, headers=headers).content)
    #     convenience.assert_marks_equal([expected_mark], email_marks)

    #     public_email_marks = json.loads(requests.get(url + "/" + email).content)
    #     convenience.assert_marks_equal([], public_email_marks)

    #     private_email_marks = json.loads(
    #         requests.get(url + "/" + email, headers=headers).content)
    #     convenience.assert_marks_equal([expected_mark], private_email_marks)

    #     specific_mark_response = requests.get(url + "/" + email + "/0")
    #     self.assertEqual(404, specific_mark_response.status_code)

    #     specific_mark_with_auth = json.loads(
    #         requests.get(url + "/" + email + "/0", headers=headers).content)
    #     convenience.assert_marks_equal(expected_mark, specific_mark_with_auth)


    # @unittest.expectedFailure
    # def test_cannot_create_public_mark_without_who_and_when(self):
    #     _, email, password = self._create_test_user()
    #     headers = {"X-Email": email, "X-Password": password}
    #     mark1 = {"~": 0, "#": "Hello"}
    #     mark2 = {"@": email, "#": "Hello"}

    #     expected_response_data = {
    #         "human_readable": "Must include @ and ~ with all marks"}

    #     url = self._base_url() + "/mark"
    #     post_data = json.dumps(mark1)
    #     response = requests.post(url, headers=headers, data=post_data)
    #     response_data = json.loads(response.content)
    #     self.assertEqual(response.status_code, 400)
    #     self.assertEqual(response_data, expected_response_data)

    #     post_data = json.dumps(mark2)
    #     response = requests.post(url, headers=headers, data=post_data)
    #     response_data = json.loads(response.content)
    #     self.assertEqual(response.status_code, 400)
    #     self.assertEqual(response_data, expected_response_data)


    # @unittest.expectedFailure
    # def test_get_public_marks_of_others_while_authed(self):
    #     _, user1, password1 = self._create_test_user()
    #     user1_headers = {"X-Email": user1, "X-Password": password1}

    #     post_data = json.dumps({"~": 0, "@": user1, "#": "Hello!"})
    #     response = requests.post(
    #         self._base_url() + "/mark", data=post_data, headers=user1_headers)
    #     self.assertEqual(response.status_code, 202)

    #     _, user2, password2 = self._create_test_user()
    #     user2_headers = {"X-Email": user2, "X-Password": password2}

    #     expected_mark = {u"#": "Hello!", u"@": user1,
    #                      u"%url": settings["RECALL_API_BASE_URL"] + u"/mark/" + user1 + "/0",
    #                      u"~": 0, u"£created": 0}

    #     response = requests.get(
    #         self._base_url() + "/mark/" + user1 + "/0", headers=user2_headers)
    #     actual_mark = json.loads(response.content)
    #     convenience.assert_marks_equal(expected_mark, actual_mark)

    #     response = requests.get(self._base_url() + "/mark/" + user1, headers=user2_headers)
    #     actual_marks = json.loads(response.content)
    #     convenience.assert_marks_equal([expected_mark], actual_marks)

    #     response = requests.get(self._base_url() + "/mark", headers=user2_headers)
    #     actual_marks = json.loads(response.content)
    #     convenience.assert_marks_equal([expected_mark], actual_marks)


    # @unittest.expectedFailure
    # def test_bulk_addition_of_marks(self):
    #     user = convenience.create_test_user()
    #     marks = [
    #         {
    #             u"~": 0,
    #             u"@": user.email,
    #             u"#": u"Hello",
    #         },
    #         {
    #             u"~": 1,
    #             u"@": user.email,
    #             u"#": u"Hello",
    #             u"%private": True
    #         }]

    #     post_response = requests.post(
    #         self._base_url() + "/mark", data=json.dumps(marks),
    #         headers=user.headers())
    #     get_response = requests.get(self._base_url() + "/mark/" + user.email,
    #                                headers=user.headers())

    #     actual_response_data = json.loads(get_response.content)
    #     for mark in actual_response_data:
    #         del mark["%url"]
    #         del mark[u"£created"]
    #     expected_response_data = list(reversed(marks))
    #     self.assertEqual(202, post_response.status_code)
    #     self.assertEqual(expected_response_data, actual_response_data)


    # @unittest.expectedFailure
    # def test_marks_with_reserved_keys_refused(self):
    #     def assertError(expected_response_data, mark):
    #         url = self._base_url() + "/mark"
    #         post_data = json.dumps(mark)
    #         response = requests.post(url, data=post_data, headers=headers)
    #         response_data = json.loads(response.content)
    #         self.assertEqual(400, response.status_code, msg=post_data)
    #         self.assertEqual(expected_response_data, response_data)

    #     _, email, password = self._create_test_user()
    #     headers = {"X-Email": email, "X-Password": password}

    #     problematic_marks = [
    #         {"~": 0, "@": email, "$problem": True},
    #         {"~": 0, "@": email, "submap": {"$problem": True}},
    #         {"~": 0, "@": email, u"£problem": True},
    #         ]
    #     expected_response_dollar = {
    #             u"human_readable": u"Mark keys may not be prefixed with $ or £",
    #             u"machine_readable": u"$problem"}
    #     expected_response_pound = {
    #             u"human_readable": u"Mark keys may not be prefixed with $ or £",
    #             u"machine_readable": u"£problem"}
    #     assertError(expected_response_dollar, problematic_marks[0])
    #     assertError(expected_response_dollar, problematic_marks[1])
    #     assertError(expected_response_pound, problematic_marks[2])


    # @unittest.expectedFailure
    # def test_get_marks_since(self):
    #     _, email, password = self._create_test_user()
    #     headers = {"X-Email": email, "X-Password": password}
    #     marks = []
    #     for time in xrange(0, 5):
    #         marks.append({"@": email, "~": time})
    #     url = self._base_url() + "/mark"
    #     post_data = json.dumps(marks)
    #     requests.post(url, data=post_data, headers=headers)

    #     url = self._base_url() + "/mark?since=1"
    #     response = requests.get(url, headers=headers)
    #     response_data = json.loads(response.content)
    #     self.assertEqual(200, response.status_code)
    #     mark_times = map(lambda mark: mark["~"], response_data)
    #     self.assertEqual([4, 3, 2], mark_times)

    #     url = self._base_url() + "/mark/%s?since=1" % email
    #     response = requests.get(url, headers=headers)
    #     response_data = json.loads(response.content)
    #     self.assertEqual(200, response.status_code)
    #     mark_times = map(lambda mark: mark["~"], response_data)
    #     self.assertEqual([4, 3, 2], mark_times)


    # @unittest.expectedFailure
    # def test_get_marks_before(self):
    #     _, email, password = self._create_test_user()
    #     headers = {"X-Email": email, "X-Password": password}
    #     marks = []
    #     for time in xrange(0, 5):
    #         marks.append({"@": email, "~": time})
    #     url = self._base_url() + "/mark"
    #     post_data = json.dumps(marks)
    #     requests.post(url, data=post_data, headers=headers)

    #     url = self._base_url() + "/mark?before=3"
    #     response = requests.get(url, headers=headers)
    #     response_data = json.loads(response.content)
    #     self.assertEqual(200, response.status_code)
    #     mark_times = map(lambda mark: mark["~"], response_data)
    #     self.assertEqual([2, 1, 0], mark_times)

    #     url = self._base_url() + "/mark/%s?before=3" % email
    #     response = requests.get(url, headers=headers)
    #     response_data = json.loads(response.content)
    #     self.assertEqual(200, response.status_code)
    #     mark_times = map(lambda mark: mark["~"], response_data)
    #     self.assertEqual([2, 1, 0], mark_times)


    # @unittest.expectedFailure
    # def test_error_handler_always_returns_json_object(self):
    #     try:
    #         raise Exception
    #     except Exception as e:
    #         data, status = old_server.handle_exception(e)
    #         self.assertIn("human_readable", json.loads(data))

    # def assert_search_results_equal(self, url, expected_marklist):
    #     response = requests.get(url)
    #     content = json.loads(response.content)
    #     self.assertEquals(200, response.status_code)
    #     self.assertNotEquals([], content)
    #     convenience.assert_marks_equal(expected_marklist, content)

    # @unittest.skip("Skipping worker tests")
    # def test_can_search_for_marks(self):
    #     user = convenience.create_test_user()
    #     mark = {"@": user.email, "~": 0, "#": "Please index me!"}
    #     convenience.post_mark(
    #         user, mark)

    #     def inner_assert():
    #         url = convenience.api_url()
    #         url += "/mark?q=index"
    #         response = requests.get(url)
    #         content = json.loads(response.content)
    #         self.assertEquals(200, response.status_code)
    #         self.assertEquals(1, len(content))
    #         convenience.assert_marks_equal(content, [mark])

    #     convenience.with_patience(inner_assert)

    # @unittest.skip("Skipping worker tests")
    # def test_cant_search_for_private_marks_anonymously(self):
    #     user = convenience.create_test_user()
    #     mark1 = {"@": user.email, "~": 0,
    #              "#": "Khajiit has no words for you", "%private": True}
    #     mark2 = {u"@": user.email, u"~": 0,
    #              u"#": u"Khajiit has some words for you"}
    #     convenience.post_mark(user, mark1)
    #     convenience.post_mark(user, mark2)


    #     url = convenience.api_url()
    #     url += "/mark?q=Khajiit"

    #     def inner_assert():
    #         response = requests.get(url)
    #         content = json.loads(response.content)
    #         self.assertEquals(200, response.status_code)
    #         convenience.assert_marks_equal([mark2], content)

    #     convenience.with_patience(inner_assert)

    # @unittest.skip("Skipping worker tests")
    # def test_can_search_for_own_private_marks(self):
    #     user1 = convenience.create_test_user()
    #     user2 = convenience.create_test_user()
    #     mark1 = {"@": user1.email, "~": 0, "#": "My secret mark",
    #              "%private": True}
    #     mark2 = {u"@": user2.email, u"~": 0,
    #              u"#": u"Someone else's secret mark",
    #              "%private": True}
    #     convenience.post_mark(user1, mark1)
    #     convenience.post_mark(user2, mark2)

    #     url = convenience.api_url()
    #     url += "/mark?q=secret"

    #     def inner_assert():
    #         response = requests.get(url, headers=user2.headers())
    #         content = json.loads(response.content)
    #         self.assertEquals(200, response.status_code)
    #         convenience.assert_marks_equal([mark2], content)

    #     convenience.with_patience(inner_assert)

    # @unittest.skip("Skipping worker tests")
    # def test_facts_are_included_with_marks(self):
    #     user = convenience.create_test_user()
    #     marks = [
    #         {"@": user.email, "~": 0, "#": "Hello, World!"},
    #         {":": {"@": user.email, "~": 0}, "~": 1, "about": "greeting",
    #          "@":user.email}]
    #     convenience.post_mark(user, marks)

    #     url = convenience.api_url() + "/mark?q=world"

    #     def inner_assert():
    #         response = requests.get(url)
    #         content = json.loads(response.content)
    #         self.assertEquals(200, response.status_code)
    #         convenience.assert_marks_equal(
    #             [{u"@": unicode(user.email), u"~": 0, u"#": u"Hello, World!",
    #               u"about": [u"greeting"]}],
    #             content)

    #     convenience.with_patience(inner_assert)

    # @unittest.skip("Skipping worker tests")
    # def test_can_browse_by_single_fact(self):
    #     user = convenience.create_test_user()
    #     marks = [
    #         {"@": user.email, "~": 3, "#": "Goodbye, Cruel World!"},
    #         {"@": user.email, "~": 0, "#": "Hello, World!"},
    #         {":": {"@": user.email, "~": 0}, "~": 1, "about": "greeting",
    #          "@": user.email},
    #         ]
    #     convenience.post_mark(user, marks)

    #     url = convenience.api_url() + "/mark?q=world&about=greeting"

    #     expected_marklist = [{u"@": unicode(user.email),
    #                           u"~": 0,
    #                           u"#": u"Hello, World!",
    #                           u"about": [u"greeting"]}]

    #     def inner_assert():
    #         response = requests.get(url)
    #         content = json.loads(response.content)
    #         self.assertEquals(200, response.status_code)
    #         self.assertNotEquals([], content)
    #         convenience.assert_marks_equal(expected_marklist, content)

    #     convenience.with_patience(inner_assert)

    # @unittest.skip("Skipping worker tests")
    # def test_can_browse_by_multiple_about_facts(self):
    #     user = convenience.create_test_user()
    #     marks = [
    #         {"@": user.email, "~": 0, "#": "Hello, World!"},
    #         {"@": user.email, "~": 2, "#": "My name is Kurt Cobain, world!"},
    #         {"@": user.email, "~": 3, "#": "Goodbye, Cruel World!"},
    #         {":": {"@": user.email, "~": 0}, "~": 4, "about": "greeting",
    #          "@": user.email},
    #         {":": {"@": user.email, "~": 2}, "~": 5, "about": "suicidal",
    #          "@": user.email},
    #         {":": {"@": user.email, "~": 3}, "~": 6, "about": "greeting",
    #          "@": user.email},
    #         {":": {"@": user.email, "~": 3}, "~": 7, "about": "suicidal",
    #          "@": user.email},
    #         ]
    #     convenience.post_mark(user, marks)

    #     url = convenience.api_url() + "/mark?q=world&about=greeting+suicidal"

    #     expected_marklist = [{u"@": unicode(user.email),
    #                           u"~": 3,
    #                           u"#": u"Goodbye, Cruel World!",
    #                           u"about": [u"greeting", u"suicidal"]}]

    #     def inner_assert():
    #         response = requests.get(url)
    #         content = json.loads(response.content)
    #         self.assertEquals(200, response.status_code)
    #         self.assertNotEquals([], content)
    #         convenience.assert_marks_equal(expected_marklist, content)

    #     convenience.with_patience(inner_assert)

    # @unittest.skip("Skipping worker tests")
    # def test_can_browse_by_not_about_facts(self):
    #     user = convenience.create_test_user()
    #     marks = [
    #         {"@": user.email, "~": 0, "#": "Hello, World!"},
    #         {"@": user.email, "~": 2, "#": "My name is Kurt Cobain, world!"},
    #         {"@": user.email, "~": 3, "#": "Goodbye, Cruel World!"},
    #         {":": {"@": user.email, "~": 0}, "~": 4, "about": "greeting",
    #          "@": user.email},
    #         {":": {"@": user.email, "~": 2}, "~": 5, "about": "suicidal",
    #          "@": user.email},
    #         {":": {"@": user.email, "~": 3}, "~": 6, "about": "greeting",
    #          "@": user.email},
    #         {":": {"@": user.email, "~": 3}, "~": 7, "about": "suicidal",
    #          "@": user.email},
    #         ]
    #     convenience.post_mark(user, marks)

    #     url = convenience.api_url() + "/mark?q=world&not_about=suicidal"

    #     expected_marklist = [{u"@": unicode(user.email),
    #                           u"~": 0,
    #                           u"#": u"Hello, World!",
    #                           u"about": [u"greeting"]}]

    #     def inner_assert():
    #         response = requests.get(url)
    #         content = json.loads(response.content)
    #         self.assertEquals(200, response.status_code)
    #         self.assertNotEquals([], content)
    #         convenience.assert_marks_equal(expected_marklist, content)

    #     convenience.with_patience(inner_assert)

    # @unittest.skip("Skipping worker tests")
    # def test_can_browse_by_multiple_not_about_facts(self):
    #     user = convenience.create_test_user()
    #     marks = [
    #         {"@": user.email, "~": 0, "#": "Hello, World!"},
    #         {"@": user.email, "~": 2, "#": "My name is Kurt Cobain, world!"},
    #         {"@": user.email, "~": 3, "#": "Goodbye, Cruel World!"},
    #         {":": {"@": user.email, "~": 0}, "~": 4, "about": "greeting",
    #          "@": user.email},
    #         {":": {"@": user.email, "~": 3}, "~": 6, "about": "greeting",
    #          "@": user.email},
    #         {":": {"@": user.email, "~": 3}, "~": 7, "about": "suicidal",
    #          "@": user.email},
    #         ]
    #     convenience.post_mark(user, marks)

    #     url = convenience.api_url() + "/mark?q=world&not_about=suicidal+greeting"

    #     expected_marklist = [{u"@": unicode(user.email),
    #                           u"~": 2,
    #                           u"#": u"My name is Kurt Cobain, world!",
    #                           }]

    #     def inner_assert():
    #         response = requests.get(url)
    #         content = json.loads(response.content)
    #         self.assertEquals(200, response.status_code)
    #         self.assertNotEquals([], content)
    #         convenience.assert_marks_equal(expected_marklist, content)

    #     convenience.with_patience(inner_assert)

    # @unittest.skip("Skipping worker tests")
    # def test_can_mix_about_and_not_about_facts(self):
    #     user = convenience.create_test_user()
    #     marks = [
    #         {"@": user.email, "~": 0, "#": "Hello, World!"},
    #         {"@": user.email, "~": 2, "#": "My name is Kurt Cobain, world!"},
    #         {"@": user.email, "~": 3, "#": "Goodbye, Cruel World!"},
    #         {":": {"@": user.email, "~": 0}, "~": 4, "about": "greeting",
    #          "@": user.email},
    #         {":": {"@": user.email, "~": 2}, "~": 4, "about": "informative",
    #          "@": user.email},
    #         {":": {"@": user.email, "~": 3}, "~": 7, "about": "greeting",
    #          "@": user.email},
    #         {":": {"@": user.email, "~": 3}, "~": 7, "about": "suicidal",
    #          "@": user.email},
    #         ]
    #     convenience.post_mark(user, marks)

    #     url = convenience.api_url() + "/mark?q=world&not_about=suicidal&about=greeting"

    #     expected_marklist = [{u"@": unicode(user.email),
    #                           u"~": 0,
    #                           u"#": u"Hello, World!",
    #                           u"about": [u"greeting"],
    #                           }]

    #     convenience.with_patience(lambda: self.assert_search_results_equal(
    #             url, expected_marklist))

    # @unittest.skip("Skipping worker tests")
    # def test_can_download_fulltext(self):
    #     user = convenience.create_test_user()
    #     marks = [{"@": user.email, "~": 0,
    #               "hyperlink": "http://localhost:8777/index.html",
    #               "title": "Hello, World!"}]
    #     convenience.post_mark(user, marks)

    #     url = convenience.api_url() + "/mark?=hippopotamus"

    #     def inner_assert():
    #         response = requests.get(url)
    #         content = json.loads(response.content)
    #         self.assertEquals(200, response.status_code)
    #         self.assertNotEquals([], content)

    #     convenience.with_patience(inner_assert)

    # @unittest.skip("Skipping worker tests")
    # def test_will_reindex_old_root_records(self):
    #     user = convenience.create_test_user()
    #     db = convenience.db()
    #     db.marks.insert({"hyperlink": "http://localhost:8777/index.html",
    #                      "@": "foobar!", "~": 0,
    #                      "£created": 0})
    #     url = convenience.api_url() + "/mark?q=hippopotamus"

    #     def inner_assert():
    #         response = requests.get(url)
    #         content = json.loads(response.content)
    #         self.assertEquals(200, response.status_code)
    #         self.assertNotEquals([], content)

    #     convenience.with_patience(inner_assert)

if __name__ == "__main__":
    unittest.main()
