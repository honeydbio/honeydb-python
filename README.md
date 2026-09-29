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

# That ASN's risk score and monthly history
honeydb asn 15169 --risk

# The monthly ASN risk report (pass --limit; the uncapped report is ~600 KB)
honeydb asn-risk --limit 25 --pretty
honeydb asn-risk --period 2026-07 --limit 25 --scanners exclude

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
| `asn <n> [--prefixes\|--risk]` | ASN organization info, its prefixes, or its risk history. |
| `asn-risk [--period YYYY-MM] [--limit N\|all] [--scanners S]` | The monthly ASN risk report. |
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
| `netinfo {lookup,network-addresses,prefixes,as-name,geolocation} <arg>` | Network info. |
| `datacenter <provider>` | Cloud/datacenter IP ranges (does not count against monthly limits). |

`ipinfo --source` values: `bogon`, `tor`, `sansip`, `ciarmy`, `et-compromised`,
`project-honeypot`, `pallebone`, `threatfox`, `blocklist_net_ua`.

`asn-risk --scanners` values: `exclude`, `only`, `include`.

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
    honeydb.create_monitors(
        [
            {
                "monitor_type": "ip_address",
                "ip_address": "196.251.81.54",
                "description": "IP Address Example",
            },
            {
                "monitor_type": "asn",
                "monitor_value": "401120",
                "description": "ASN Example",
            },
        ]
    )
    monitors = honeydb.monitors()
    honeydb.delete_monitors([m["id"] for m in monitors])
```

### ASN risk

```python
with Client("api_id", "api_key") as honeydb:
    # Call with no period first: available_months lists the periods you can ask
    # for, and it is attached only to a successful response.
    report = honeydb.asn_risk(limit=25)
    months = report["available_months"]

    july = honeydb.asn_risk(period=months[-1], limit=25, scanners="exclude")
    history = honeydb.asn_risk_history(15169)
```

Both methods return parsed JSON: an object on success. Read the notes below
before consuming either.

- **An empty list means no data.** Both endpoints answer `200 []` when the data
  does not exist — no report for the requested month, or the ASN was not scored
  anywhere in the six-month look-back window. This is deliberate API policy: a
  missing object is never a 404. Branch on emptiness before subscripting, since
  the return value is a `dict`-or-`[]` union.
- **Discover periods from the response, not by guessing.** `available_months`
  lists every month the API holds a report for, newest first — but the API
  attaches it only to a *successful* report response, so a wrong `period` gets
  you a bare `[]` with no month list. Call with no `period` first, then request
  a specific month.
- **Branch on `methodology.version`.** Reports come in two generations, `"1.0"`
  (July 2026) and `"2.0"` (August 2026 onward), which carry different row
  fields. The client passes the document through untouched and does not
  normalize between them, so check the version rather than assuming a field
  exists.
- **`scanners` only does anything on 2.0 reports.** The `scanner` row flag it
  filters on exists only on 2.0 rows. Against a 1.0 report, `exclude` is a
  silent no-op and `only` returns a *full report document* whose `asns` is `[]`
  and `asns_returned` is `0` — a third response shape, distinct from both the
  success object and the `200 []` no-data case.
- **`summary` describes the whole month**, not the rows you got back. It is
  computed before the `scanners` and `limit` filters are applied, so
  `asns_scored`, the score histogram, `score_median`, `score_p90` and
  `top_by_component` cover the full report even when you asked for 25 rows.
- **Ranks are not renumbered** by filtering or capping, so a filtered view still
  shows each ASN's true rank in the month.
- **Pass a `limit` interactively.** The uncapped default report is roughly
  600 KB of JSON.

Both calls count against your monthly request limit.

## API reference

The `Client` exposes one method per endpoint, grouped below.

- **Bad hosts:** `bad_hosts(mydata=False)`, `bad_hosts_by_service(service, mydata=False)`
- **IP context:** `ip(ip)`, `ip_geo(ip)`, `ip_netinfo(ip)`, `ip_threatinfo(ip)`,
  `ip_internet_scanner(ip)`, `ip_history(ip)`, `ip_cve(ip)`, `ip_cidr(cidr)`
- **ASN:** `asn(n)`, `asn_prefixes(n)`, `asn_risk(period=None, limit=None, scanners=None)`,
  `asn_risk_history(n)`, `asns()`, `asns_7d()`
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
- **Net info (counts against monthly limits):** `netinfo_lookup(ip)`, `netinfo_network_addresses(cidr)`,
  `netinfo_prefixes(asn)`, `netinfo_as_name(asn)`, `netinfo_geolocation(ip)`
- **Datacenter (does not count against monthly limits):** `datacenter(provider)`

See the [HoneyDB API documentation](https://honeydb.io/threats) for endpoint details and
response formats, including which endpoints do not count against your monthly quota.

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
