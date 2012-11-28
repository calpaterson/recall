import json
import time
from datetime import datetime, timedelta

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
    stop_trying = datetime.now() + timedelta(seconds=5)
    while True:
        try:
            with open(settings["RECALL_MAILFILE"], "r") as mail_file:
                for line in mail_file:
                    if "verify-email" in line:
                        verify_url = line.strip()
            break
        except IOError:
            if datetime.now() > stop_trying:
                assert False, "didn't get the email"

    response = requests.post(
        url=verify_url,
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
