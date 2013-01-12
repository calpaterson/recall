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

"""This module provides an easy way to create Logger objects without the need
to faff with the logging module."""

import logging
import os
import sys
import datetime

import pytz

class _TimeZoneFormatter_(logging.Formatter):
    def formatTime(self, record, unused_datefmt=None):
        """Return a string representation of the time that record was created
        including time offset information.  The date format argument is ignored.

        """
        dt = datetime.datetime.fromtimestamp(record.created)
        localised_dt = _timezone_.localize(dt)
        return localised_dt.isoformat()

_log_debug_messages_ = False
def log_debug_messages():
    """Change the log level of all loggers to DEBUG (even those previously
    returned)"""
    global _log_debug_messages_
    _log_debug_messages_ = True
    for name in _loggers_:
        _loggers_[name].setLevel(logging.DEBUG)

_logging_enabled_ = True

def disable_logging():
    """Remove all handlers from all loggers (even though previously
    returned)"""
    global _logging_enabled_
    _logging_enabled_ = False
    for name in _loggers_:
        _loggers_[name].handlers = []

_loggers_ = {}

def get(name):
    """Return the logger by that name.

    This function will always return the same logger for the same name (the
    removes the possibility of some messages being duplicated).

    The logger will print with the correct timezone information if the TZ
    variable is set and exported and with UTC otherwise.  In both cases, it
    will include proper time offset information.

    The logger will print to standard out.

    Unless log_debug_messages has been called, the logger will only print
    messages of INFO level and above.

    """
    if name not in _loggers_:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_TimeZoneFormatter_(_log_format_))
        logger = logging.getLogger(name)
        if _log_debug_messages_:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
        if _logging_enabled_:
            logger.addHandler(handler)
        _loggers_[name] = logger
    return _loggers_[name]

_log_format_ = "%(levelname)s:%(name)s:%(asctime)s:%(process)d:%(message)s"

_formatter_ = logging.Formatter(_log_format_)

_timezone_ = pytz.utc
try:
    _timezone_ = pytz.timezone(os.environ["TZ"])
except pytz.exceptions.UnknownTimeZoneError:
    get(__name__).error("Unknown timezone: {tz} - using UTC instead".format(
            tz=os.environ["TZ"]))
except KeyError:
    get(__name__).warn("No TZ variable set - using UTC instead")
