#!/usr/bin/env python

import os

import requests

import convenience

settings = convenience.settings

def main():
    os.environ["RECALL_DEBUG_MODE"] = "1"
    convenience.load_settings()
    convenience.wipe_mongodb()
    convenience.wipe_elastic_search()
    convenience.create_test_user(fixture_user=True)
    db = convenience.get_db()
    db.users.insert({
            "surname" : "Paterson",
            "firstName" : "Cal",
            "registered" : 0,
            "email_key" : "f0e5aab5-f938-48df-8937-f33ff187e976",
            "email" : "unverified_user@example.com"})

if __name__ == "__main__":
    main()
