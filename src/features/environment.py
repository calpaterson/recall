import os

import behave
from recall import convenience, search

def before_all(context):
    convenience.no_logging()
    convenience.load_settings()
    context.config.log_capture = False

def before_feature(context, feature):
    try:
        os.remove(convenience.settings["RECALL_MAILFILE"])
    except OSError:
        pass

    convenience.wipe_mongodb()
    search.clear()
