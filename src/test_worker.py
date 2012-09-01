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

import requests

import convenience

class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.tearDown()

    def tearDown(self):
        convenience.wipe_mongodb()
        convenience.wipe_elastic_search()

    def assert_search_results_equal(self, url, expected_marklist):
        response = requests.get(url)
        content = json.loads(response.content)
        self.assertEquals(200, response.status_code)
        self.assertNotEquals([], content)
        convenience.assert_marks_equal(expected_marklist, content)

    def test_can_search_for_marks(self):
        user = convenience.create_test_user()
        mark = {"@": user.email, "~": 0, "#": "Please index me!"}
        convenience.post_mark(
            user, mark)

        def inner_assert():
            url = convenience.api_url()
            url += "/mark?q=index"
            response = requests.get(url)
            content = json.loads(response.content)
            self.assertEquals(200, response.status_code)
            self.assertEquals(1, len(content))
            convenience.assert_marks_equal(content, [mark])

        convenience.with_patience(inner_assert)

    def test_cant_search_for_private_marks_anonymously(self):
        user = convenience.create_test_user()
        mark1 = {"@": user.email, "~": 0,
                 "#": "Khajiit has no words for you", "%private": True}
        mark2 = {u"@": user.email, u"~": 0,
                 u"#": u"Khajiit has some words for you"}
        convenience.post_mark(user, mark1)
        convenience.post_mark(user, mark2)


        url = convenience.api_url()
        url += "/mark?q=Khajiit"

        def inner_assert():
            response = requests.get(url)
            content = json.loads(response.content)
            self.assertEquals(200, response.status_code)
            convenience.assert_marks_equal([mark2], content)

        convenience.with_patience(inner_assert)

    def test_can_search_for_own_private_marks(self):
        user1 = convenience.create_test_user()
        user2 = convenience.create_test_user()
        mark1 = {"@": user1.email, "~": 0, "#": "My secret mark",
                 "%private": True}
        mark2 = {u"@": user2.email, u"~": 0,
                 u"#": u"Someone else's secret mark",
                 "%private": True}
        convenience.post_mark(user1, mark1)
        convenience.post_mark(user2, mark2)

        url = convenience.api_url()
        url += "/mark?q=secret"

        def inner_assert():
            response = requests.get(url, headers=user2.headers())
            content = json.loads(response.content)
            self.assertEquals(200, response.status_code)
            convenience.assert_marks_equal([mark2], content)

        convenience.with_patience(inner_assert)

    def test_facts_are_included_with_marks(self):
        user = convenience.create_test_user()
        marks = [
            {"@": user.email, "~": 0, "#": "Hello, World!"},
            {":": {"@": user.email, "~": 0}, "~": 1, "about": "greeting",
             "@":user.email}]
        convenience.post_mark(user, marks)

        url = convenience.api_url() + "/mark?q=world"

        def inner_assert():
            response = requests.get(url)
            content = json.loads(response.content)
            self.assertEquals(200, response.status_code)
            convenience.assert_marks_equal(
                [{u"@": unicode(user.email), u"~": 0, u"#": u"Hello, World!",
                  u"about": [u"greeting"]}],
                content)

        convenience.with_patience(inner_assert)

    def test_can_browse_by_single_fact(self):
        user = convenience.create_test_user()
        marks = [
            {"@": user.email, "~": 3, "#": "Goodbye, Cruel World!"},
            {"@": user.email, "~": 0, "#": "Hello, World!"},
            {":": {"@": user.email, "~": 0}, "~": 1, "about": "greeting",
             "@": user.email},
            ]
        convenience.post_mark(user, marks)

        url = convenience.api_url() + "/mark?q=world&about=greeting"

        expected_marklist = [{u"@": unicode(user.email),
                              u"~": 0,
                              u"#": u"Hello, World!",
                              u"about": [u"greeting"]}]

        def inner_assert():
            response = requests.get(url)
            content = json.loads(response.content)
            self.assertEquals(200, response.status_code)
            self.assertNotEquals([], content)
            convenience.assert_marks_equal(expected_marklist, content)

        convenience.with_patience(inner_assert)

    def test_can_browse_by_multiple_about_facts(self):
        user = convenience.create_test_user()
        marks = [
            {"@": user.email, "~": 0, "#": "Hello, World!"},
            {"@": user.email, "~": 2, "#": "My name is Kurt Cobain, world!"},
            {"@": user.email, "~": 3, "#": "Goodbye, Cruel World!"},
            {":": {"@": user.email, "~": 0}, "~": 4, "about": "greeting",
             "@": user.email},
            {":": {"@": user.email, "~": 2}, "~": 5, "about": "suicidal",
             "@": user.email},
            {":": {"@": user.email, "~": 3}, "~": 6, "about": "greeting",
             "@": user.email},
            {":": {"@": user.email, "~": 3}, "~": 7, "about": "suicidal",
             "@": user.email},
            ]
        convenience.post_mark(user, marks)

        url = convenience.api_url() + "/mark?q=world&about=greeting+suicidal"

        expected_marklist = [{u"@": unicode(user.email),
                              u"~": 3,
                              u"#": u"Goodbye, Cruel World!",
                              u"about": [u"greeting", u"suicidal"]}]

        def inner_assert():
            response = requests.get(url)
            content = json.loads(response.content)
            self.assertEquals(200, response.status_code)
            self.assertNotEquals([], content)
            convenience.assert_marks_equal(expected_marklist, content)

        convenience.with_patience(inner_assert)

    def test_can_browse_by_not_about_facts(self):
        user = convenience.create_test_user()
        marks = [
            {"@": user.email, "~": 0, "#": "Hello, World!"},
            {"@": user.email, "~": 2, "#": "My name is Kurt Cobain, world!"},
            {"@": user.email, "~": 3, "#": "Goodbye, Cruel World!"},
            {":": {"@": user.email, "~": 0}, "~": 4, "about": "greeting",
             "@": user.email},
            {":": {"@": user.email, "~": 2}, "~": 5, "about": "suicidal",
             "@": user.email},
            {":": {"@": user.email, "~": 3}, "~": 6, "about": "greeting",
             "@": user.email},
            {":": {"@": user.email, "~": 3}, "~": 7, "about": "suicidal",
             "@": user.email},
            ]
        convenience.post_mark(user, marks)

        url = convenience.api_url() + "/mark?q=world&not_about=suicidal"

        expected_marklist = [{u"@": unicode(user.email),
                              u"~": 0,
                              u"#": u"Hello, World!",
                              u"about": [u"greeting"]}]

        def inner_assert():
            response = requests.get(url)
            content = json.loads(response.content)
            self.assertEquals(200, response.status_code)
            self.assertNotEquals([], content)
            convenience.assert_marks_equal(expected_marklist, content)

        convenience.with_patience(inner_assert)

    def test_can_browse_by_multiple_not_about_facts(self):
        user = convenience.create_test_user()
        marks = [
            {"@": user.email, "~": 0, "#": "Hello, World!"},
            {"@": user.email, "~": 2, "#": "My name is Kurt Cobain, world!"},
            {"@": user.email, "~": 3, "#": "Goodbye, Cruel World!"},
            {":": {"@": user.email, "~": 0}, "~": 4, "about": "greeting",
             "@": user.email},
            {":": {"@": user.email, "~": 3}, "~": 6, "about": "greeting",
             "@": user.email},
            {":": {"@": user.email, "~": 3}, "~": 7, "about": "suicidal",
             "@": user.email},
            ]
        convenience.post_mark(user, marks)

        url = convenience.api_url() + "/mark?q=world&not_about=suicidal+greeting"

        expected_marklist = [{u"@": unicode(user.email),
                              u"~": 2,
                              u"#": u"My name is Kurt Cobain, world!",
                              }]

        def inner_assert():
            response = requests.get(url)
            content = json.loads(response.content)
            self.assertEquals(200, response.status_code)
            self.assertNotEquals([], content)
            convenience.assert_marks_equal(expected_marklist, content)

        convenience.with_patience(inner_assert)

    def test_can_mix_about_and_not_about_facts(self):
        user = convenience.create_test_user()
        marks = [
            {"@": user.email, "~": 0, "#": "Hello, World!"},
            {"@": user.email, "~": 2, "#": "My name is Kurt Cobain, world!"},
            {"@": user.email, "~": 3, "#": "Goodbye, Cruel World!"},
            {":": {"@": user.email, "~": 0}, "~": 4, "about": "greeting",
             "@": user.email},
            {":": {"@": user.email, "~": 2}, "~": 4, "about": "informative",
             "@": user.email},
            {":": {"@": user.email, "~": 3}, "~": 7, "about": "greeting",
             "@": user.email},
            {":": {"@": user.email, "~": 3}, "~": 7, "about": "suicidal",
             "@": user.email},
            ]
        convenience.post_mark(user, marks)

        url = convenience.api_url() + "/mark?q=world&not_about=suicidal&about=greeting"

        expected_marklist = [{u"@": unicode(user.email),
                              u"~": 0,
                              u"#": u"Hello, World!",
                              u"about": [u"greeting"],
                              }]

        convenience.with_patience(lambda: self.assert_search_results_equal(
                url, expected_marklist))

    def test_can_download_fulltext(self):
        user = convenience.create_test_user()
        marks = [{"@": user.email, "~": 0,
                  "hyperlink": "http://localhost:8777/index.html",
                  "title": "Hello, World!"}]
        convenience.post_mark(user, marks)

        url = convenience.api_url() + "/mark?=hippopotamus"

        def inner_assert():
            response = requests.get(url)
            content = json.loads(response.content)
            self.assertEquals(200, response.status_code)
            self.assertNotEquals([], content)

        convenience.with_patience(inner_assert)

    def test_will_reindex_old_root_records(self):
        user = convenience.create_test_user()
        db = convenience.db()
        db.marks.insert({"hyperlink": "http://localhost:8777/index.html",
                         "@": "foobar!", "~": 0,
                         "£created": 0})
        url = convenience.api_url() + "/mark?q=hippopotamus"

        def inner_assert():
            response = requests.get(url)
            content = json.loads(response.content)
            self.assertEquals(200, response.status_code)
            self.assertNotEquals([], content)

        convenience.with_patience(inner_assert)

if __name__ == "__main__":
    unittest.main()
