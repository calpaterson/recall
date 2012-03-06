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
from io import BytesIO

import requests
import gpgme

CALPATERSON_API_HOST = "api.recall.calpaterson.com"
LOCALHOST_API = "localhost:5000"

TYPES = { "location": {"latitude": float,
                       "longitude": float}}

def get_location():
    print "Longitude [-0.2046306]:",
    longitude = raw_input()
    if longitude == "":
        longitude = float("-0.2046306")
    else:
        longitude = float(raw_input())

    print "Latitude [51.5341945]:",
    latitude = raw_input()
    if latitude == "":
        latitude = float("51.5341945")
    else:
        latitude = float(raw_input())
    return latitude, longitude

def get_what_and_where():
    print "Say [%s]:" % "I'm an idiot",
    what = raw_input()
    print "Which server [%s]?:" % LOCALHOST_API,
    where = raw_input()
    if where == "":
        where = LOCALHOST_API
    where = "http://" + where + "/mark"
    return what, where

def sign_mark(mark):
    mark_bytes = BytesIO(json.dumps(mark))

    ctx = gpgme.Context()
    sign = BytesIO("")

    ctx.sign(mark_bytes, sign, gpgme.SIG_MODE_CLEAR)
    mark["signatures"] = [sign.getvalue()]
    return mark

def main():
    what, where = get_what_and_where()
    # mark = {
    #     "#": what,
    #     "~": int(time.time()),
    #     "@": "cal@calpaterson.com"
    #     }
    lat, longi = get_location()
    mark = {
        "latitude": lat,
        "longitude": longi,
        "~": int(time.time()),
        "@": "cal@calpaterson.com"
        }
    mark_json = json.dumps(sign_mark(mark))
    response = requests.post(
        where,
        data=mark_json,
        headers={"Content-Type": "application/json"})
    try:
        j = json.loads(response.content)
        print j["url"]
    except Exception as e:
        print response.content
        print "Failed"
        print e
        exit(1)

if __name__ == "__main__":
    main()
