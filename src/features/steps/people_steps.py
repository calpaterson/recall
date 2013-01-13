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

from datetime import datetime, timedelta
import json
import os
import re
import time

from behave import *
from hamcrest import *
import requests

from recall.convenience import settings

def _people_url():
    return "http://" + settings["RECALL_API_HOST"] + ":" +\
      settings["RECALL_API_PORT"] + "/" + "people/"

@when("i sign up")
def step(context):
    context.email_shadow = "example@recall.calpaterson.com"
    context.private_email = "foo@bar.com"
    response = requests.post(
        url=_people_url() + context.email_shadow + "/",
        data=json.dumps({
            "firstName": "Example",
            "surname": "Example",
            "token": "t1",
            "private_email": context.private_email,
            }),
        headers={"content-type": "application/json"})
    assert_that(response.status_code, is_(202))

@then("i get an email")
def step(context):
    time.sleep(0.5)
    with open(settings["RECALL_MAILFILE"], "r") as mail_file:
        contents = mail_file.read()
        email_key =  re.search(r"[a-z0-9\-]{36}", contents).group()
        assert_that(contents, contains_string(context.private_email))

    response = requests.post(
        url=_people_url() + "example" + "/" + email_key,
        data=json.dumps({"password": "password"}),
        headers={"content-type": "application/json"})
    assert_that(response.status_code, is_(201))

    context.user = response.json


@then("i have an account")
def step(context):
    response = requests.get(
        url=_people_url() + context.user["email"] + "/",
        headers={"content-type": "application/json"})
    assert_that(response.status_code, is_(200))


@then("only i can see my private email address")
def step(context):
    url = _people_url() + context.user["email"] + "/"
    public_response = requests.get(
        url=url,
        headers={"content-type": "application/json"})
    private_response = requests.get(
        url=url + "self",
        headers={"content-type": "application/json",
                 "x-email": context.user["email"],
                 "x-password": "password"})

    assert_that(public_response.text, not(contains_string(
        context.private_email)))
    assert_that(private_response.text, contains_string(
        context.private_email))
