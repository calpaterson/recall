import json
from UserDict import DictMixin
import inspect

from bottle import request, response, abort
from pygments import highlight
from pygments.lexers.web import JSONLexer
from pygments.formatters import HtmlFormatter
import bcrypt

import convenience as conv

def mimetypes(header_contents):
    """Returns a list of allowed mimetypes based on the Accept header"""
    for entry in header_contents.split(","):
        subentries = entry.split(";")
        yield subentries[0].strip()

def html_pretty_print(json_string):
    """Formats JSON nicely for browsers"""
    return highlight(json_string, JSONLexer(),
              HtmlFormatter(full=True, linenos="table"))

class PPJSONPlugin(object):
    api = 2

    def apply(self, callback, context):
        def wrapper(*args, **kwargs):
            if request.json is None and request.body.len != 0:
                abort(400)
            return_value = callback(*args, **kwargs)
            return_value = json.dumps(return_value, indent=4)
            if "text/html" in mimetypes(request.headers.get("Accept")):
                return_value = html_pretty_print(as_string)
            else:
                response.set_header("Content-Type", "application/json")
            return return_value
        return wrapper

ppjson = PPJSONPlugin()

class HeadersPlugin(object):
    api = 2

    def apply(self, callback, content):
        def wrapper(*args, **kwargs):
            return_value = callback(*args, **kwargs)
            response.set_header("Server", "Recall")
            return return_value
        return wrapper

headers = HeadersPlugin()

class PretendHandlerDict(object, DictMixin):
    def __handler__(self, error):
        return json.dumps({"human_readable": error.output})

    def keys(self):
        return xrange(400, 600)

    def __getitem__(self, key):
        return self.__handler__

    def __setitem__(self, key, value):
        raise NotImplementedError("PretendHandlerDict is not a real dictionary")

    def __delitem__(self, key):
        __setitem__(self, None, None)

class AuthenticationPlugin(object):
    api = 2
    kwarg = "user"

    def __init__(self):
        self.logger = conv.logger("AuthenticationPlugin")

    def user(self):
        headers = request.headers
        try:
            email = headers["X-Email"]
            password = headers["X-Password"]
            user = conv.db().users.find_one(
                {"email": email, "password_hash": {"$exists": True}})
        except KeyError:
            return None
        self.check(user, password)
        return user

    def check(self, user, password):
        expected_hash = user["password_hash"]
        actual_hash = bcrypt.hashpw(password, user["password_hash"])
        if expected_hash != actual_hash:
            self.logger.warn("{email} tried wrong password".format(
                    email=user["email"]))
            abort(403, "Email or password or both do not match")
        else:
            self.logger.debug("{email} authenticated".format(
                    email=user["email"]))

    def apply(self, callback, context):
        expected_args = inspect.getargspec(context.callback)[0]
        if self.kwarg not in expected_args:
            return callback
        else:
            def wrapper(*args, **kwargs):
                user = self.user()
                if user is not None:
                    kwargs[self.kwarg] = user
                return callback(*args, **kwargs)
            return wrapper

auth = AuthenticationPlugin()
