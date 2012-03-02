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

def main():
    example_data = json.dumps({
            "#": "Hello, World!",
            "~": int(time.time()),
            "@": "cal@calpaterson.com"
            })
    response = requests.post(
        "http://api.recall.calpaterson.com/mark",
        data=json.dumps(example_data),
        headers={"Content-Type": "application/json"})
    try:
        print response.content
        j = json.loads(response.content)
        print j["url"]
    except:
        print "Failed"

if __name__ == "__main__":
    main()
