#!/usr/bin/env python

import convenience as c
import jobs

def main():
    c.load_settings()
    logger = c.logger("reindex_all_bookmarks")
    db = c.db()
    records = db.marks.find({":": {"$exists": False}})
    number = records.count()
    count = 1
    for record in records:
        logger.info("{count} of {number} {who}/{when}".format(
                count=count,
                number=number,
                who=record["@"],
                when=record["~"]))
        logger.debug(type(record["~"]))
        jobs.enqueue(jobs.IndexRecord(record))
        count += 1
    logger.info("Done")

if __name__ == "__main__":
    main()
