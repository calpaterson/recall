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

import uuid

from bottle import Bottle, request, response, abort
import bcrypt

from recall.data import whitelist, blacklist
from recall import convenience as c
from recall import plugins
from recall import jobs
from recall import paymill

app = Bottle()
app.install(plugins.ppjson)
app.install(plugins.auth)
app.install(plugins.cors)
app.error_handler = plugins.handler_dict

logger = c.logger("people")

@app.get("/")
def users():
    abort(503, "Not yet implemented")

@app.get("/<who>/")
def user_(who):
    try:
        return whitelist(c.db().users.find_one({"email": who}), [
                "email",
                "firstName",
                ])
    except AttributeError:
        logger.warn("Asked about {email}, but that is not a user".format(email=who))
        abort(404, "User not found")

@app.get("/<who>/self")
def self_(who, user):
    if who != user["email"]:
        response.status = 400

@app.post("/<who>/")
def request_invite(who):
    # FIXME: Don't allow the pseudonym "public"
    user = whitelist(request.json, [
            "pseudonym",
            "firstName",
            "surname",
            "email",
            "token",
            ])
    if "email" not in user:
        return "You must provide an email field", 400
    user["email_key"] = str(uuid.uuid4())
    user["registered"] = c.unixtime()
    c.db().users.ensure_index("email", unique=True)
    c.db().users.insert(user, safe=True)
    response.status = 202
    logger.info("{email} subscribed".format(email=who))
    jobs.enqueue(paymill.StartBilling(user["email"], user["token"]))

@app.post("/<who>/<email_key>")
def verify_email(who, email_key):
    # FIXME: Need to harden this code:
    # Information leaks between wrong email and email already existing
    # if who != request.json["email"]:
    #     abort(400, "You can only verify your own email")
    if "RECALL_TEST_MODE" in c.settings or "RECALL_DEBUG_MODE" in c.settings:
        salt = bcrypt.gensalt(1)
    else:
        salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(request.json["password"], salt)

    spec = {"email_key": email_key, "email": request.json["email"],
            "verified": {"$exists": False}}
    update = {"$set": {"password_hash": password_hash,
                       "verified": c.unixtime()}}
    success = c.db().users.update(spec, update, safe=True)["updatedExisting"]
    if not success:
        if c.db().users.find_one({"email_key": email_key, "email": request.json["email"]}):
            logger.warn("{email} tried to verify a second time".format(email=who))
            abort(403, "Already verified")
        else:
            user = c.db().users.find_one({"email": who})
            if user is not None:
                right_key = user["email_key"]
                logger.warn("{email} tried to verify with {wrong_key} but should use {right_key}".format(
                        email=who, wrong_key = email_key, right_key=right_key))
                abort(404, "No such email_key or wrong email")
            else:
                logger.warn("{email} tried to verify with {email_key}, but " +
                            "never requested an invite.".format(
                        email=who, email_key=email_key))
                abort(404, "No such email_key or wrong email")
    user = c.db().users.find_one({"email_key": email_key})
    response.status = 201
    return blacklist(user, ["_id", "email_key", "password_hash"])
