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

def whitelist(dict_, whitelist):
    d = {}
    for k, v in list(dict_.items()):
        if k in whitelist:
            d[k] = v
    return d

def blacklist(dict_, blacklist):
    d = {}
    for k, v in list(dict_.items()):
        if k not in blacklist:
            d[k] = v
    return d

def has_problematic_keys(mark):
    mark_queue = []
    current = mark
    while True:
        for key in current:
            if key.startswith("$") or key.startswith("£"):
                return True
            if isinstance(current[key], dict):
                mark_queue.insert(0, current[key])
        if mark_queue == []:
            return False
        else:
            current = mark_queue.pop()

def strip_generated_keys(bookmarks):
    """Delete all keys that start with £ or $ from a bookmark"""
    if bookmarks is None:
        return
    for bookmark in bookmarks:
        keys = list(bookmark.keys())
        for key in keys:
            if key.startswith("£") or key.startswith("%"):
                del bookmark[key]
