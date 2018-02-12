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
import datetime
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
    honeydb = api.Client(api_id, api_key)

    try:
        # Get bad hosts
        bad_hosts = honeydb.bad_hosts()
        out(bad_hosts)

        # Get sensor data count
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        data_count = honeydb.sensor_data_count(sensor_data_date=today)
        out(data_count)

        # Get sensor data
        data = honeydb.sensor_data(sensor_data_date=today)
        out(data)

        """
        # Example with from_id.
        # See more information on using from_id here:
        # https://riskdiscovery.com/honeydb/#sensor_data_filtered
        data = honeydb.sensor_data(sensor_data_date=today, from_id=84869618)
        out(data)
        """

        # Get threat bin
        threatbin = honeydb.threatbin()
        out(threatbin)

        # Get twitter threat feed
        twitter = honeydb.twitter_threat_feed()
        out(twitter)

        """
        # Example with ipaddress.
        # See more information on using from_id here:
        # https://riskdiscovery.com/honeydb/#twitter_threat_feed
        twitter = honeydb.twitter_threat_feed(ipaddress="201.179.21.139")
        out(twitter)
        """

    except Exception as error:
        print(str(error))


if __name__ == '__main__':
    main()
