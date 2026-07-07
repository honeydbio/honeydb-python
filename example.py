#!/usr/bin/env python3
"""Example usage of the HoneyDB API client.

Credentials are read from environment variables:

    export HONEYDB_API_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    export HONEYDB_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
"""

import datetime
import json
import os

from honeydb import Client, HoneyDBError


def out(data: object) -> None:
    """Pretty-print JSON data."""
    print(json.dumps(data, indent=2, sort_keys=True))


def main() -> None:
    api_id = os.environ["HONEYDB_API_ID"]
    api_key = os.environ["HONEYDB_API_KEY"]

    # The client is a context manager so its connection pool is cleaned up.
    with Client(api_id, api_key) as honeydb:
        try:
            # Bad hosts seen across the honeypot network in the last 24 hours.
            out(honeydb.bad_hosts())

            # Full context for an IP address (netinfo, threat, history, ...).
            out(honeydb.ip("8.8.8.8"))

            # Check an IP against known IP lists.
            out(honeydb.ipinfo("8.8.8.8"))
            out(honeydb.ipinfo_source("tor", "8.8.8.8"))

            # Network info lookups do not count against your monthly limit.
            out(honeydb.netinfo_as_name(15169))

            # Your own sensor data for today.
            today = datetime.date.today().isoformat()
            out(honeydb.sensor_data_count(today))
            out(honeydb.sensor_data(today))

            # Manage monitors.
            out(honeydb.monitors())
            # honeydb.create_monitors([
            #     {"monitor_type": "asn", "monitor_value": "401120",
            #      "description": "ASN Example"},
            # ])
            # honeydb.delete_monitors([122, 123])

        except HoneyDBError as error:
            print(f"HoneyDB API error: {error}")


if __name__ == "__main__":
    main()
