#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

import convenience
import jobs

settings = convenience.settings

logger = None

def term_handler(unused_signum, unused_frame):
    logger.info("Shutting down")

def main():
    global logger
    convenience.load_settings()
    logger = convenience.logger("worker")
    logger.info("Starting with settings: {settings}".format(
            settings=settings))
    signal.signal(signal.SIGTERM, term_handler)
    while(True):
        try:
            jobs.dequeue().do()
        except Exception as e:
            logger.exception(e)

if __name__ == "__main__":
    main()
