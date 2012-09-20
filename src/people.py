import uuid
import json

from bottle import Bottle, request, response, abort
import bcrypt

from data import whitelist, blacklist
from convenience import unixtime, db, settings
import convenience
import plugins

app = Bottle()
app.install(plugins.ppjson)
app.install(plugins.auth)
app.install(plugins.cors)
app.error_handler = plugins.PretendHandlerDict()

logger = convenience.logger("people")

@app.get("/")
def users():
    abort(503, "Not yet implemented")

@app.get("/<who>/")
def user_(who):
    try:
        return whitelist(db().users.find_one({"email": who}), [
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
    body = whitelist(request.json, [
            "pseudonym",
            "firstName",
            "surname",
            "email",
            ])
    if "email" not in body:
        return "You must provide an email field", 400
    body["email_key"] = str(uuid.uuid4())
    body["registered"] = unixtime()
    db().users.ensure_index("email", unique=True)
    db().users.insert(body, safe=True)
    response.status = 202
    logger.info("{email} requested an invite".format(email=who))

@app.post("/<who>/<email_key>")
def verify_email(who, email_key):
    # FIXME: Need to harden this code:
    # Information leaks between wrong email and email already existing
    # if who != request.json["email"]:
    #     abort(400, "You can only verify your own email")
    if "RECALL_TEST_MODE" in settings or "RECALL_DEBUG_MODE" in settings:
        salt = bcrypt.gensalt(1)
    else:
        salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(request.json["password"], salt)

    spec = {"email_key": email_key, "email": request.json["email"],
            "verified": {"$exists": False}}
    update = {"$set": {"password_hash": password_hash,
                       "verified": unixtime()}}
    success = db().users.update(spec, update, safe=True)["updatedExisting"]
    if not success:
        if db().users.find_one({"email_key": email_key, "email": request.json["email"]}):
            logger.warn("{email} tried to verify a second time".format(email=who))
            abort(403, "Already verified")
        else:
            user = db().users.find_one({"email": who})
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
    user = db().users.find_one({"email_key": email_key})
    response.status = 201
    return blacklist(user, ["_id", "email_key", "password_hash"])
