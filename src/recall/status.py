#!/usr/bin/env python
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

from bottle import Bottle, error, response

from recall import (
    plugins,
    convenience as conv,
    jobs,
    search
    )

app = Bottle()
app.install(plugins.ppjson)
app.install(plugins.auth)
app.install(plugins.cors)

@app.get("/")
def status():
    status_dict = {
        "job_queue": jobs.status(),
        "search": search.status()
        }
    for key in status_dict:
        if status_dict[key] != "ok":
            response.status = 500
    return status_dict
