import behave
from recall import convenience

def before_all(context):
    convenience.no_logging()
    convenience.load_settings()
    context.config.log_capture = False
