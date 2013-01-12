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

import os

import convenience

settings = convenience.settings

def main():
    os.environ["RECALL_DEBUG_MODE"] = "1"
    convenience.load_settings()
    convenience.wipe_mongodb()
    convenience.wipe_elastic_search()
    convenience.create_test_user(fixture_user=True)
    db = convenience.db()
    db.users.insert({
            "surname" : "Paterson",
            "firstName" : "Cal",
            "registered" : 0,
            "email_key" : "f0e5aab5-f938-48df-8937-f33ff187e976",
            "email" : "unverified_user@example.com"})

if __name__ == "__main__":
    main()
