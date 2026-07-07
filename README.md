# honeydb-python

[![Format, Lint & Test](https://github.com/honeydbio/honeydb-python/actions/workflows/format-lint.yml/badge.svg?branch=master)](https://github.com/honeydbio/honeydb-python/actions/workflows/format-lint.yml?query=branch%3Amaster)
[![PyPI version](https://img.shields.io/pypi/v/honeydb.svg)](https://pypi.org/project/honeydb/)
[![Python versions](https://img.shields.io/pypi/pyversions/honeydb.svg)](https://pypi.org/project/honeydb/)

A Python API wrapper and command-line tool for the [HoneyDB](https://honeydb.io) API.

HoneyDB provides real-time threat intelligence collected from a distributed network of
honeypots — bad hosts, IP reputation, ASN activity, CVE sightings, network info, cloud/datacenter
IP ranges, and more.

- **Full API coverage** — every current HoneyDB endpoint is exposed.
- **Modern & typed** — Python 3.10+, full type hints, ships a `py.typed` marker.
- **Robust HTTP** — pooled `requests.Session` with automatic retries and typed exceptions.
- **Ergonomic CLI** — a git-style subcommand interface: `honeydb ip 8.8.8.8`.

## Requirements

- Python 3.10+
- A HoneyDB API ID and API key ([sign in](https://honeydb.io) to get yours).

## Installation

```bash
pip install honeydb
```

## Authentication

All requests require an API ID and API key. Provide them via environment variables:

```bash
export HONEYDB_API_ID=<your api id>
export HONEYDB_API_KEY=<your api key>
```

The CLI also accepts `--api-id` / `--api-key`, and the library takes them as constructor
arguments.

## CLI usage

```bash
# Bad hosts seen in the last 24 hours
honeydb bad-hosts

# Full context for an IP (pretty-printed)
honeydb ip 8.8.8.8 --pretty

# Just the geolocation view of that IP
honeydb ip 8.8.8.8 --geo

# ASN organization + its prefixes
honeydb asn 15169
honeydb asn 15169 --prefixes

# Check an IP against a specific list
honeydb ipinfo 185.220.101.1 --source tor

# Cloud/datacenter IP ranges (does not count against monthly limits)
honeydb datacenter aws

# Your own sensor data for a date
honeydb sensor-data --date 2025-04-01
honeydb sensor-data --date 2025-04-01 --count

# Manage monitors
honeydb monitors list
honeydb monitors create --json '[{"monitor_type":"asn","monitor_value":"401120","description":"ASN Example"}]'
honeydb monitors delete --id 122 123
```

Run `honeydb --help` or `honeydb <command> --help` for the full command tree. Global flags
`--pretty/-p` and `--timeout` apply to any command. Output is JSON on stdout; errors go to
stderr with a non-zero exit code.

### Commands

| Command | Description |
| --- | --- |
| `bad-hosts [--service S] [--mydata]` | Bad hosts (last 24h), optionally by service. |
| `ip <ip> [--geo\|--netinfo\|--threatinfo\|--scanner\|--history\|--cve]` | IP context, or a single view. |
| `ip-cidr <cidr>` | All IP addresses within a network range. |
| `asn <n> [--prefixes]` | ASN organization info or its prefixes. |
| `asns [--days 1\|7]` | ASNs seen in the last 1 (default) or 7 days. |
| `cve <cve>` | IP history for a CVE. |
| `cve-ip <ip>` | CVE history for an IP. |
| `sensor-data --date D [--from-id ID] [--count] [--all]` | Your sensor event data for a date. |
| `services` | Emulated services (last 24h). |
| `stats --year Y --month M` | Summary stats for a year/month. |
| `monitors {list,logs,notifications,create,delete}` | Manage monitors. |
| `nodes [--mydata]` | honeydb-agent nodes (last 3 days). |
| `payload-history {remote-hosts,attributes,...}` | Payload history data. |
| `internet-scanner <ip> [--info]` | Whether an IP is a known internet scanner. |
| `ipinfo <ip> [--source SRC]` | Check an IP against known IP lists. |
| `netinfo {lookup,network-addresses,prefixes,as-name,geolocation} <arg>` | Network info (no monthly limit). |
| `datacenter <provider>` | Cloud/datacenter IP ranges (no monthly limit). |

`ipinfo --source` values: `bogon`, `tor`, `sansip`, `ciarmy`, `et-compromised`,
`project-honeypot`, `pallebone`, `threatfox`, `blocklist_net_ua`.

`datacenter` providers: `aws`, `azure`, `azure/china`, `azure/germany`, `azure/gov`,
`cloudflare`, `gcp`, `ibm`, `oracle`.

## Library usage

```python
from honeydb import Client

with Client("api_id", "api_key") as honeydb:
    hosts = honeydb.bad_hosts()
    context = honeydb.ip("8.8.8.8")
    is_tor = honeydb.ipinfo_source("tor", "185.220.101.1")
    ranges = honeydb.datacenter("aws")
```

The client can also be used without the context manager (call `.close()` when done), and
you can pass a shared `requests.Session`, a custom `timeout`, or a different `base_url`:

```python
client = Client("api_id", "api_key", timeout=10, retries=5)
try:
    print(client.services())
finally:
    client.close()
```

### Error handling

Every failed request raises a typed exception, all subclasses of `HoneyDBError`:

```python
from honeydb import (
    Client,
    HoneyDBError,
    HoneyDBAuthError,
    HoneyDBNotFoundError,
    HoneyDBRateLimitError,
)

with Client("api_id", "api_key") as honeydb:
    try:
        honeydb.ip("8.8.8.8")
    except HoneyDBAuthError:
        print("Check your API credentials.")
    except HoneyDBRateLimitError as error:
        print(f"Rate limited; retry after {error.retry_after}s")
    except HoneyDBError as error:
        print(f"Request failed with HTTP {error.status_code}: {error}")
```

### Monitors

```python
with Client("api_id", "api_key") as honeydb:
    honeydb.create_monitors([
        {"monitor_type": "ip_address", "ip_address": "196.251.81.54",
         "description": "IP Address Example"},
        {"monitor_type": "asn", "monitor_value": "401120",
         "description": "ASN Example"},
    ])
    monitors = honeydb.monitors()
    honeydb.delete_monitors([m["id"] for m in monitors])
```

## API reference

The `Client` exposes one method per endpoint, grouped below.

- **Bad hosts:** `bad_hosts(mydata=False)`, `bad_hosts_by_service(service, mydata=False)`
- **IP context:** `ip(ip)`, `ip_geo(ip)`, `ip_netinfo(ip)`, `ip_threatinfo(ip)`,
  `ip_internet_scanner(ip)`, `ip_history(ip)`, `ip_cve(ip)`, `ip_cidr(cidr)`
- **ASN:** `asn(n)`, `asn_prefixes(n)`, `asns()`, `asns_7d()`
- **CVE:** `cve(cve)`, `cve_ip(ip)`
- **Sensor data:** `sensor_data(date, from_id=None, mydata=True)`, `sensor_data_count(date, mydata=True)`
- **Services / stats:** `services()`, `stats(year, month)`
- **Monitors:** `monitors()`, `create_monitors(list)`, `delete_monitors(ids)`,
  `monitors_logs()`, `monitors_notifications()`
- **Nodes:** `nodes(mydata=False)`
- **Payload history:** `payload_history_remote_hosts()`, `payload_history_attributes()`,
  `payload_history_attribute(attr)` (plus API-deprecated helpers)
- **Internet scanner:** `internet_scanner(ip)`, `internet_scanner_info(ip)`
- **IP info lists:** `ipinfo(ip)`, `ipinfo_source(source, ip)`
- **Net info (no monthly limit):** `netinfo_lookup(ip)`, `netinfo_network_addresses(cidr)`,
  `netinfo_prefixes(asn)`, `netinfo_as_name(asn)`, `netinfo_geolocation(ip)`
- **Datacenter (no monthly limit):** `datacenter(provider)`

See the [HoneyDB API documentation](https://honeydb.io/threats) for endpoint details and
response formats.

## Migrating from v1.x

v2.0.0 is a ground-up rewrite. Notable changes:

- **New import surface.** `from honeydb import Client` (the `from honeydb import api;
  api.Client(...)` form still works).
- **The CLI is now subcommand-based.** For example, `honeydb --bad-hosts` becomes
  `honeydb bad-hosts`, and `honeydb --netinfo-lookup 1.2.3.4` becomes
  `honeydb netinfo lookup 1.2.3.4`.
- **Replaced endpoints were dropped** in favor of their modern equivalents:
  the old `ip_history()` / `ip-context` top-level methods are replaced by `ip()` and
  `ip_history()` under the `/ip/<ip>` family, and `stats_asn()` is replaced by `asns()`.
- **Errors now raise typed exceptions** (`HoneyDBError` and subclasses) instead of returning
  raw response bodies.

## Development

```bash
make env           # create .env venv and install with dev extras
make format        # ruff format
make lint          # ruff check
make test          # pytest (uses mocked HTTP, no API keys needed)
make build         # build sdist + wheel
```

This project uses [ruff](https://docs.astral.sh/ruff/) for both formatting and linting.

## License

MIT — see [LICENSE](LICENSE).
