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

import requests

from recall.convenience import settings
from recall import jobs
from recall import convenience


class UpstreamError(Exception):
    def __init__(self, response):
        Exception.__init__(self, repr(
            {"message": response.text,
             "status_code": response.status_code,
             "form": response.request.data}))


class OurError(Exception):
    def __init__(self, response):
        Exception.__init__(self, repr(
            {"message": response.text,
             "status_code": response.status_code,
             "form": response.request.data}))


def _url():
    return settings["RECALL_PAYMILL_URL"]


def _auth():
    return settings["RECALL_PAYMILL_PRIVATE_KEY"], "no_password"


def _handle_failure(response):
    if 400 <= response.status_code <= 499:
        raise OurError(response)
    elif 500 <= response.status_code <= 599:
        raise UpstreamError(response)


def _create_client(user):
    form = {"email": user["email"]}
    response = requests.post(
        _url() + "clients", verify=False, auth=_auth(), data=form)
    _handle_failure(response)
    return response.json["data"]["id"]


def _create_credit_card(token, client_identifier):
    form = {"client": client_identifier, "token": token}
    response = requests.post(
        _url() + "payments", verify=False, auth=_auth(), data=form)
    _handle_failure(response)
    return response.json["data"]["id"]


def _create_subscription(client_identifier, credit_card_identifier):
    offer_identifier = settings["RECALL_PAYMILL_OFFER"]
    form = {
        "client": client_identifier,
        "offer": offer_identifier,
        "payment": credit_card_identifier
    }
    response = requests.post(
        _url() + "subscriptions", verify=False, auth=_auth(), data=form)
    _handle_failure(response)
    return response.json["data"]["id"]


def _start_billing(user, token):
    """Begin billing a user in Paymill, returning Paymill's identifiers.

    Register the user as a client in Paymill.  Attach the credit card
    details the token refers to to that client.  Subscribe the user to
    the offer (from settings).

    No guarantee is given that the user has been billed"""
    client_identifier = _create_client(user)
    credit_card_identifier = _create_credit_card(token, client_identifier)
    subscription_identifier = _create_subscription(client_identifier,
                                                   credit_card_identifier)
    return {"client_identifier": client_identifier,
            "credit_card_identifier": credit_card_identifier,
            "subscription_identifier": subscription_identifier}


def _has_been_recently_billed(user):
    """Return True if a recent billing can be found, False otherwise."""
    response = requests.get(
        _url() + "transactions", verify=False, auth=_auth())
    _handle_failure(response)
    client_identifier = user["paymill"]["client_identifier"]
    transactions = response.json["data"]
    for transaction in transactions:
        print(transactions)
        if transaction["client"]["id"] == client_identifier:
            return transaction["status"] == "closed"
    return False


class StartBilling(jobs.Job):
    def __init__(self, email, token):
        assert type(email) == str
        assert type(token) == str
        self.email = email
        self.token = token

    def do(self):
        logger = convenience.logger("StartBilling")
        user = convenience.db().users.find_one({"email": self.email})
        user["paymill"] = _start_billing(user, self.token)
        convenience.db().users.save(user, safe=True)
        logger.info("Started billing " + user["email"])
        jobs.enqueue(CheckBilling(user), priority=3)


class CheckBilling(jobs.Job):
    def __init__(self, user, last_noted=datetime.now()):
        assert type(user) == dict
        self.user = user
        self.last_noted = last_noted

    def do(self):
        logger = convenience.logger("CheckBilling")
        if _has_been_recently_billed(self.user):
            logger.info("Billing for {email} went through".format(
                email=self.user["email"]))
            jobs.enqueue(jobs.SendInvite(self.user))
        else:
            if self.last_noted < (datetime.now() - timedelta(hours=1)):
                email = self.user["email"]
                # send some message it's all going wrong!
                logger.warn(
                    "Billing for {email} has not happened in last hour".format(
                        email=email))
                jobs.enqueue(CheckBilling(self.user), priority=3)
            else:
                logger.debug(
                    "Billing for {email} has not happened".format(
                        email=email))
                jobs.enqueue(CheckBilling(
                    self.user, self.last_noted=last_noted), priority=3)
