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

import json
import time

import requests

CALPATERSON_API_HOST = "api.recall.calpaterson.com"

def main():
    print "Say:",
    comment = raw_input()
    print "Where?:",
    where = raw_input()
    if where == "":
        where = CALPATERSON_API_HOST
    where = "http://" + where + "/mark"
    example_data = json.dumps({
            "#": comment,
            "~": int(time.time()),
            "@": "cal@calpaterson.com"
            })
    print example_data
    response = requests.post(
        where,
        data=json.dumps(example_data),
        headers={"Content-Type": "application/json"})
    try:
        j = json.loads(response.content)
        print j["url"]
    except Exception as e:
        print "Failed"
        print e
        exit(1)

if __name__ == "__main__":
    main()
