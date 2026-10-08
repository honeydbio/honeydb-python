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

# The same list as CSV, saved to a file
honeydb bad-hosts --format csv > bad-hosts.csv

# Full context for an IP (pretty-printed)
honeydb ip 8.8.8.8 --pretty

# Just the geolocation view of that IP
honeydb ip 8.8.8.8 --geo

# ASN organization + its prefixes
honeydb asn 15169
honeydb asn 15169 --prefixes

# That ASN's risk score, known-scanner status and monthly history
honeydb asn 15169 --risk

# The monthly ASN risk report (pass --limit; the uncapped report is ~600 KB)
honeydb asn-risk --limit 25 --pretty
honeydb asn-risk --period 2026-07 --limit 25

# Known internet scanners are reported separately; this returns that report
honeydb asn-risk --scanners only --pretty

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
| `bad-hosts [--service S] [--mydata] [--format json\|csv]` | Bad hosts (last 24h), optionally by service or as CSV. |
| `ip <ip> [--geo\|--netinfo\|--threatinfo\|--scanner\|--history\|--cve]` | IP context, or a single view. |
| `ip-cidr <cidr>` | All IP addresses within a network range. |
| `asn <n> [--prefixes\|--risk]` | ASN organization info, its prefixes, or its risk history and known-scanner status. |
| `asn-risk [--period YYYY-MM] [--limit N\|all] [--scanners S]` | The monthly ASN risk report: the ranking, or the separate known-scanner report. |
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

`asn-risk --scanners` values: `exclude`, `only`, `include`. Known internet scanners
are excluded from the ranking and reported separately as benign activity: `only`
returns that scanner report, `exclude` and `include` return the ranking.

`bad-hosts --format csv` prints the CSV exactly as the API returns it (header
`remote_host,count,last_seen`), byte for byte, as UTF-8 with `\n` line endings on
every platform. `--pretty` has no effect on it. `--service` and `--mydata` requests
are JSON only and ignore `--format`.

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

### Bad hosts as CSV

Pass `format="csv"` to get the bad-hosts list as CSV text instead of parsed JSON:

```python
with Client("api_id", "api_key") as honeydb:
    csv_text = honeydb.bad_hosts(format="csv")

with open("bad-hosts.csv", "w", encoding="utf-8", newline="") as handle:
    handle.write(csv_text)
```

- The return value is a `str` holding the CSV as the API sent it (header
  `remote_host,count,last_seen`). It is not parsed.
- With `mydata=True` the format is ignored: the API serves own-sensor data as JSON
  only, so parsed JSON is returned. `bad_hosts_by_service()` is JSON only too.
- The API prefixes `'` to cells that a spreadsheet could read as a formula. The
  client leaves that in place.
- If the API cannot produce the CSV it answers `503`. With the default session the
  client retries 3 times, waiting the `Retry-After` the API sends (about 90 seconds
  in total), and then raises `HoneyDBError` with `status_code` 503 and `retry_after`
  set. Pass a lower `retries` to `Client` to fail faster. A session you pass in
  yourself is not retried by the library.

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

Every `HoneyDBError` has a `retry_after` attribute: the seconds to wait from the
API's `Retry-After` header, or `None` if the API did not send one.

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
    if report:  # an empty list means no report
        months = report["available_months"]
        for row in report["asns"]:  # the ranking: known scanners are not in it
            print(row["rank"], row["asn"], row["risk_score"])

        # From August 2026 on, known scanners are reported separately. The
        # scanner report rides along on every response, whatever `scanners` is.
        if report["methodology"].get("scanner_handling") == "separate_report":
            scanners = report["scanner_report"]
            print(scanners["risk_assessment"], scanners["statement"])
            for row in scanners["asns"]:  # activity rows: no risk_score or rank
                print(row["asn"], row["scanner"]["name"], row["observed_ips"])

    # Or ask for the scanner report as the rows themselves.
    only = honeydb.asn_risk(limit=25, scanners="only")
    if only and only.get("asns_report") == "scanners":
        print(only["asns_total"], "known scanner ASNs this month")

    # One ASN: not seen, known scanner, or ranked.
    result = honeydb.asn_risk_history(398324)
    if not result:
        print("not seen in the look-back window")
    elif result.get("known_scanner"):
        scanner = result["known_scanner"]
        current = scanner["period"] == result["latest_month"]
        print(scanner["name"], scanner["risk_assessment"], "current:", current)
    elif result["latest"]:
        print(result["latest"]["rank"], result["latest"]["risk_score"])
```

Both methods return parsed JSON: an object on success. The client passes the
document through untouched. Read the notes below before consuming either.

- **An empty list means no data.** Both endpoints answer `200 []` when the data
  does not exist — no report for the requested month, or the ASN is in neither
  the ranking nor the scanner report anywhere in the six-month look-back
  window. This is deliberate API policy: a missing object is never a 404. The
  return value is a `dict`-or-`[]` union, so check emptiness **first**, before
  subscripting or calling `.get()`.
- **Discover periods from the response, not by guessing.** `available_months`
  lists every month the API holds a report for, newest first — but the API
  attaches it only to a *successful* report response, so a wrong `period` gets
  you a bare `[]` with no month list. Call with no `period` first, then request
  a specific month.
- **Known scanners are excluded from the ranking and reported separately.**
  From the August 2026 report on, ASNs operated by known internet scanners
  (research and attack-surface-management crawlers) are not ranked and not
  risk-scored. They are listed in a separate `scanner_report`, whose
  `risk_assessment` is `"benign"` and whose `statement` explains that the
  activity is considered relatively benign and very low to no risk.
- **Branch on the report generation.** July 2026 is `methodology.version`
  `"1.0"`: no `scanner_report`, and rows without `percentile`, `services_seen`
  or `prior`. August 2026 onward is `"2.0"` with
  `methodology.scanner_handling == "separate_report"` — check that marker
  rather than assuming a field exists.
- **`scanners` selects a report.** From August 2026 on, `only` puts the scanner
  report's rows in `asns`; omitting it, `include` and `exclude` all return the
  ranking (`exclude` and `include` are kept for compatibility and change
  nothing). On the July 2026 report there is no scanner report: `exclude` and
  `include` are no-ops and `only` returns a full report document whose `asns`
  is `[]` and `asns_returned` is `0`.
- **`asns_report` says which rows you got**: `"ranking"` or `"scanners"`. It
  was added on 2026-09-30, so use `.get()` if your code may also read responses
  saved before then.
- **Scanner rows are activity rows, not ranked rows.** They carry `asn`,
  `entity`, `scanner` (`{name, url}`), `observed_ips`, `announced_ipv4_space`,
  `density`, `days_seen` and `services_seen`. The `risk_score`, `rank`,
  `percentile`, `components` and `prior` keys are *absent*, not `null` — so
  `row["risk_score"]` raises `KeyError` on a `scanners="only"` response.
- **`asns_total` and `asns_returned`.** `asns_returned` is the number of rows
  in `asns`. `asns_total` is the size of the selected report before `limit`:
  for August 2026, 3,218 for the ranking and 10 for `scanners="only"`. On the
  July 2026 report `asns_total` is the full ranked count whatever `scanners`
  is, so `only` there reports a non-zero total with zero rows.
- **`scanner_report` is on every response from August 2026 on**, whatever
  `scanners` is, with `risk_assessment`, `statement`, `scanner_list_version`,
  `asns_observed` and `asns`. `limit` caps the top-level `asns` only;
  `scanner_report.asns` is always complete. `summary.scanners_observed` is its
  row count.
- **`summary` describes the whole month's ranking**, not the rows you got back.
  It covers ranked (non-scanner) ASNs only and is unaffected by `limit` and
  `scanners`, so `asns_scored`, the score histogram, `score_median`,
  `score_p90` and `top_by_component` cover the full ranking even when you asked
  for 25 rows.
- **Ranks are among non-scanner ASNs and are not renumbered** by `limit`, so a
  capped view still shows each ASN's true rank in the month.
- **Deprecated keys.** `summary.scanners_tagged` and each ranked row's
  `scanner` key are always `null`. Do not rely on either.
- **`known_scanner` on the per-ASN call.** The top-level `known_scanner` is
  `null`, or an object (`name`, `url`, `risk_assessment`, `statement`,
  `scanner_list_version`, `period`) for the *newest month in the look-back in
  which the ASN was a known scanner*. That is not necessarily `latest_month`,
  so compare `known_scanner.period` with it: an ASN taken off the scanner list
  has a ranked `latest` and an older `known_scanner.period`, and an ASN not
  seen in the latest month but a scanner earlier has `latest: null` with
  `known_scanner` set.
- **`latest` and `history` for a scanner.** When the ASN is a known scanner in
  the latest month, `latest` is its activity row (no `rank`, `risk_score` or
  `percentile`). Each `history` entry carries a boolean `known_scanner` — the
  same name as the top-level object, but a flag. Entries for scanner months
  have `null` rank, score and percentile; months where the ASN was ranked keep
  their numbers. Months where the ASN is in neither list are omitted, so
  `history` can be shorter than `months_checked`.
- **Pass a `limit` interactively.** The uncapped default report is roughly
  600 KB of JSON.

Both calls count against your monthly request limit.

## API reference

The `Client` exposes one method per endpoint, grouped below.

- **Bad hosts:** `bad_hosts(mydata=False, *, format=None)`, `bad_hosts_by_service(service, mydata=False)`
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
