from behave import *
from hamcrest import *

import requests

from recall import convenience

@when("i am a user")
def step(context):
    context.user = convenience.create_test_user()

@then("my email address is private")
def step(context):
    response = requests.get(convenience.new_url() + context.user.id + "/self")
    assert_that(response.json["email"], none)
