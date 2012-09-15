import json

from bottle import request, response
from pygments import highlight
from pygments.lexers.web import JSONLexer
from pygments.formatters import HtmlFormatter

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
    name = "PPJSONPlugin"

    def apply(self, callback, context):
        def wrapper(*args, **kwargs):
            if request.json is None and request.body.len != 0:
                abort(400)
            return_value = callback(*args, **kwargs)
            as_string = json.dumps(return_value, indent=4)
            if "text/html" in mimetypes(request.headers.get("Accept")):
                return html_pretty_print(as_string),
            else:
                response.content_type = "application/json"
                return as_string
        return wrapper

ppjson = PPJSONPlugin()

class Headers(object):
    api = 2
    name = "Headers"

    def apply(self, callback, content):
        def wrapper(*args, **kwargs):
            return_value = callback(*args, **kwargs)
            response.set_header("Server", "Recall")
            return return_value
        return wrapper

headers = Headers()
