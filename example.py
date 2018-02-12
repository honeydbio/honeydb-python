#!/usr/bin/env python
"""
Example script for using the HoneyDB API client

In this example, API credentials must be exported to environment variables:
export HONEYDB_API_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
export HONEYDB_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
"""

from __future__ import print_function
import os
import json
from honeydb import api


def out(json_data):
    """
    Output json data in pretty format
    """
    print(json.dumps(json_data, indent=4))

def main():
    """
    The main fuction for executing example code
    """

    # Get API keys from environment variables and create the
    # HoneyDB Client API object.
    api_id = os.environ["HONEYDB_API_ID"]
    api_key = os.environ["HONEYDB_API_KEY"]
    honeydb = api.Client(keyid, secret)

    # Get bad hosts
    bad_hosts = honeydb.bad_hosts()
    out(bad_hosts)

if __name__ == '__main__':
    main()
