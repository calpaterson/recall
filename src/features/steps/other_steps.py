from hamcrest import *
from behave import *
import requests

from recall import convenience

@when("i create a public bookmark")
def step(context):
    context.public_bookmark = {
        "@": context.user.username,
        "~": 0,
        "#": "Hello, World!"
        }
    convenience.post_mark(context.user, context.public_bookmark)

@then("i can see my public bookmark")
def step(context):
    context.response = requests.get(
        convenience.new_url() + context.user.username + "/self",
        headers=context.user.headers())
    assert_that(context.response.json, is_(context.public_bookmark))

@then("i can't see my email address in the bookmark")
def step(context):
    assert_that(context.response.text, is_not(contains_string(context.user.email)))
