#!/usr/bin/env python
"""
honeydb CLI tool

API credentials must be exported to environment variables:
export HONEYDB_API_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
export HONEYDB_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
"""

from __future__ import print_function
import os
import sys
import json
import argparse
from honeydb import api


def print_json_data(json_data, pretty=False):
    """
    Print JSON data, with option of pretty printing
    """
    if pretty:
        print(json.dumps(json_data, indent=4))
    else:
        print(json.dumps(json_data))


def main():
    """
    Main function for HoneyDB CLI tool
    """
    try:
        api_id = os.environ["HONEYDB_API_ID"]
        api_key = os.environ["HONEYDB_API_KEY"]
    except KeyError as error:
        print("Environment variable not set {}".format(str(error)))
        exit()

    # Create honeydb object
    honeydb = api.Client(api_id, api_key)

    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Process command line arguments.")

    parser.add_argument(
        '--bad-hosts',
        help='Get bad hosts.',
        default=False,
        action="store_true")
    parser.add_argument(
        '--sensor-data-count',
        help='Get sensor data count.',
        default=False,
        action="store_true")
    parser.add_argument(
        '--sensor-data',
        help='Get sensor data.',
        default=False,
        action="store_true")
    parser.add_argument(
        '--threatbin',
        help='Get ThreatBin entires.',
        default=False,
        action="store_true")
    parser.add_argument(
        '--twitter-threat-feed',
        help='Get Twitter Theat Feed.',
        default=False,
        action="store_true")
    parser.add_argument(
        '--mydata',
        help='Filter on mydata.',
        default=False,
        action="store_true")
    parser.add_argument(
        '--date',
        help='Date in format YYYY-MM-DD')
    parser.add_argument(
        '--ip-address',
        help='IP address to filter on.')
    parser.add_argument(
        '--from-id',
        help='ID to continue retrieving sensor data.')
    parser.add_argument(
        '--pretty',
        help='Print JSON in pretty format.',
        default=False,
        action="store_true")

    args = parser.parse_args()

    if args.bad_hosts:
        print_json_data(honeydb.bad_hosts(), args.pretty)

    if args.sensor_data_count:
        if not args.date:
            print('--date argument required.')
            sys.exit()
        
        print_json_data(honeydb.sensor_data_count(args.date), args.pretty)
        
    if args.sensor_data:
        if not args.date:
            print('--date argument required.')
            sys.exit()
        
        if not args.from_id:
            print_json_data(honeydb.sensor_data(args.date), args.pretty)
        else:
            print_json_data(honeydb.sensor_data(args.date, from_id=args.from_id), args.pretty)

    if args.threatbin:
        print_json_data(honeydb.threatbin(), args.pretty)

    if args.twitter_threat_feed:
        if not args.ip_address:
            print_json_data(honeydb.twitter_threat_feed(), args.pretty)
        else:
            print_json_data(honeydb.twitter_threat_feed(ipaddress=args.ip_address), args.pretty)


if __name__ == '__main__':
    main()