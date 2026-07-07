"""Command-line interface for the HoneyDB API.

Credentials are read from ``--api-id`` / ``--api-key`` or, if not given, from
the ``HONEYDB_API_ID`` / ``HONEYDB_API_KEY`` environment variables.

Run ``honeydb --help`` to see the available commands.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from typing import Any

from honeydb import __version__
from honeydb.api.client import DATACENTER_PROVIDERS, IPINFO_SOURCES, Client
from honeydb.exceptions import HoneyDBError

PROG = "honeydb"


def emit(data: Any, pretty: bool) -> None:
    """Print JSON data, optionally pretty-printed."""
    if pretty:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(json.dumps(data))


# --------------------------------------------------------------------------
# Command handlers. Each takes (client, args) and returns the API response.
# --------------------------------------------------------------------------


def _cmd_bad_hosts(client: Client, args: argparse.Namespace) -> Any:
    if args.service:
        return client.bad_hosts_by_service(args.service, mydata=args.mydata)
    return client.bad_hosts(mydata=args.mydata)


def _cmd_ip(client: Client, args: argparse.Namespace) -> Any:
    dispatch = {
        "geo": client.ip_geo,
        "netinfo": client.ip_netinfo,
        "threatinfo": client.ip_threatinfo,
        "scanner": client.ip_internet_scanner,
        "history": client.ip_history,
        "cve": client.ip_cve,
    }
    if args.view:
        return dispatch[args.view](args.ip_address)
    return client.ip(args.ip_address)


def _cmd_ip_cidr(client: Client, args: argparse.Namespace) -> Any:
    return client.ip_cidr(args.cidr)


def _cmd_asn(client: Client, args: argparse.Namespace) -> Any:
    if args.prefixes:
        return client.asn_prefixes(args.as_number)
    return client.asn(args.as_number)


def _cmd_asns(client: Client, args: argparse.Namespace) -> Any:
    return client.asns_7d() if args.days == 7 else client.asns()


def _cmd_cve(client: Client, args: argparse.Namespace) -> Any:
    return client.cve(args.cve)


def _cmd_cve_ip(client: Client, args: argparse.Namespace) -> Any:
    return client.cve_ip(args.ip_address)


def _cmd_sensor_data(client: Client, args: argparse.Namespace) -> Any:
    if args.count:
        return client.sensor_data_count(args.date, mydata=args.mydata)
    return client.sensor_data(args.date, from_id=args.from_id, mydata=args.mydata)


def _cmd_services(client: Client, _args: argparse.Namespace) -> Any:
    return client.services()


def _cmd_stats(client: Client, args: argparse.Namespace) -> Any:
    return client.stats(year=args.year, month=args.month)


def _cmd_monitors(client: Client, args: argparse.Namespace) -> Any:
    if args.action == "list":
        return client.monitors()
    if args.action == "logs":
        return client.monitors_logs()
    if args.action == "notifications":
        return client.monitors_notifications()
    if args.action == "create":
        payload = _load_json_arg(args.file, args.json)
        if not isinstance(payload, list):
            payload = [payload]
        return client.create_monitors(payload)
    if args.action == "delete":
        return client.delete_monitors(args.id)
    raise ValueError(f"Unknown monitors action: {args.action}")


def _cmd_nodes(client: Client, args: argparse.Namespace) -> Any:
    return client.nodes(mydata=args.mydata)


def _cmd_payload_history(client: Client, args: argparse.Namespace) -> Any:
    action = args.action
    if action == "remote-hosts":
        return client.payload_history_remote_hosts()
    if action == "attributes":
        if args.attribute:
            return client.payload_history_attribute(args.attribute)
        return client.payload_history_attributes()
    if action == "year":
        return client.payload_history(args.year, args.month)
    if action == "services":
        return client.payload_history_services()
    if action == "service":
        return client.payload_history_service(args.name)
    if action == "hash":
        return client.payload_history_hash(args.value)
    raise ValueError(f"Unknown payload-history action: {action}")


def _cmd_internet_scanner(client: Client, args: argparse.Namespace) -> Any:
    if args.info:
        return client.internet_scanner_info(args.ip_address)
    return client.internet_scanner(args.ip_address)


def _cmd_ipinfo(client: Client, args: argparse.Namespace) -> Any:
    if args.source:
        return client.ipinfo_source(args.source, args.ip_address)
    return client.ipinfo(args.ip_address)


def _cmd_netinfo(client: Client, args: argparse.Namespace) -> Any:
    dispatch = {
        "lookup": client.netinfo_lookup,
        "network-addresses": client.netinfo_network_addresses,
        "prefixes": client.netinfo_prefixes,
        "as-name": client.netinfo_as_name,
        "geolocation": client.netinfo_geolocation,
    }
    return dispatch[args.action](args.value)


def _cmd_datacenter(client: Client, args: argparse.Namespace) -> Any:
    return client.datacenter(args.provider)


def _load_json_arg(file: str | None, raw: str | None) -> Any:
    """Load JSON payload from a file, an inline string, or stdin ('-')."""
    if file:
        if file == "-":
            return json.load(sys.stdin)
        with open(file, encoding="utf-8") as handle:
            return json.load(handle)
    if raw:
        return json.loads(raw)
    raise SystemExit("error: provide --file or --json with the monitor definition")


# --------------------------------------------------------------------------
# Parser construction
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    # Global options live on a shared parent parser (with SUPPRESS defaults) so
    # they may be given either before or after the subcommand, e.g. both
    # ``honeydb --pretty services`` and ``honeydb services --pretty`` work.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--api-id",
        default=argparse.SUPPRESS,
        help="HoneyDB API ID (default: HONEYDB_API_ID env var).",
    )
    common.add_argument(
        "--api-key",
        default=argparse.SUPPRESS,
        help="HoneyDB API key (default: HONEYDB_API_KEY env var).",
    )
    common.add_argument(
        "-p",
        "--pretty",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Pretty-print JSON output.",
    )
    common.add_argument(
        "--timeout",
        type=float,
        default=argparse.SUPPRESS,
        help="Per-request timeout in seconds (default: 30).",
    )

    parser = argparse.ArgumentParser(
        prog=PROG,
        parents=[common],
        description="CLI for the HoneyDB API (https://honeydb.io).",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    # Defaults are resolved in main() via getattr rather than set_defaults, so
    # that a value given before the subcommand is not clobbered by the
    # subparser (a known argparse interaction with parent parsers).

    sub = parser.add_subparsers(dest="command", metavar="<command>")

    def add(name: str, **kwargs: Any) -> argparse.ArgumentParser:
        return sub.add_parser(name, parents=[common], **kwargs)

    # bad-hosts
    p = add("bad-hosts", help="Get bad hosts (last 24h).")
    p.add_argument("--service", help="Filter by service/protocol name.")
    p.add_argument("--mydata", action="store_true", help="Only data from your sensors.")
    p.set_defaults(func=_cmd_bad_hosts)

    # ip
    p = add("ip", help="Get context for an IP address.")
    p.add_argument("ip_address", help="IP address to look up.")
    view = p.add_mutually_exclusive_group()
    for name, flag in (
        ("geo", "--geo"),
        ("netinfo", "--netinfo"),
        ("threatinfo", "--threatinfo"),
        ("scanner", "--scanner"),
        ("history", "--history"),
        ("cve", "--cve"),
    ):
        view.add_argument(
            flag,
            dest="view",
            action="store_const",
            const=name,
            help=f"Return only the {name} view.",
        )
    p.set_defaults(func=_cmd_ip, view=None)

    # ip-cidr
    p = add("ip-cidr", help="Get all IPs within a CIDR range.")
    p.add_argument("cidr", help="Network range in CIDR notation.")
    p.set_defaults(func=_cmd_ip_cidr)

    # asn
    p = add("asn", help="Get ASN organization info.")
    p.add_argument("as_number", help="Autonomous System number.")
    p.add_argument(
        "--prefixes", action="store_true", help="Return IP prefixes for the ASN."
    )
    p.set_defaults(func=_cmd_asn)

    # asns
    p = add("asns", help="List ASNs seen interacting with the network.")
    p.add_argument(
        "--days",
        type=int,
        choices=(1, 7),
        default=1,
        help="Window in days: 1 (previous day, default) or 7.",
    )
    p.set_defaults(func=_cmd_asns)

    # cve
    p = add("cve", help="Get IP history for a CVE.")
    p.add_argument("cve", help="CVE identifier, e.g. CVE-2021-44228.")
    p.set_defaults(func=_cmd_cve)

    # cve-ip
    p = add("cve-ip", help="Get CVE history for an IP.")
    p.add_argument("ip_address", help="IP address to look up.")
    p.set_defaults(func=_cmd_cve_ip)

    # sensor-data
    p = add("sensor-data", help="Get your sensor event data for a date.")
    p.add_argument("--date", required=True, help="Date in YYYY-MM-DD format.")
    p.add_argument("--from-id", dest="from_id", help="Continue paging from this id.")
    p.add_argument(
        "--count", action="store_true", help="Return a count instead of records."
    )
    p.add_argument(
        "--all",
        dest="mydata",
        action="store_false",
        help="Query all sensor data instead of only yours.",
    )
    p.set_defaults(func=_cmd_sensor_data, mydata=True)

    # services
    p = add("services", help="List emulated services (last 24h).")
    p.set_defaults(func=_cmd_services)

    # stats
    p = add("stats", help="Get summary stats for a year/month.")
    p.add_argument("--year", type=int, required=True, help="Year, e.g. 2024.")
    p.add_argument("--month", type=int, required=True, help="Month (1-12).")
    p.set_defaults(func=_cmd_stats)

    # monitors
    p = add("monitors", help="Manage monitors.")
    msub = p.add_subparsers(dest="action", metavar="<action>", required=True)

    def madd(name: str, **kwargs: Any) -> argparse.ArgumentParser:
        return msub.add_parser(name, parents=[common], **kwargs)

    madd("list", help="List current monitors.")
    madd("logs", help="Show monitor logs.")
    madd("notifications", help="Show monitor notifications.")
    mc = madd("create", help="Create monitor(s) from JSON.")
    mc.add_argument("--file", help="Path to a JSON file ('-' for stdin).")
    mc.add_argument("--json", help="Inline JSON monitor definition.")
    md = madd("delete", help="Delete monitor(s) by id.")
    md.add_argument("--id", type=int, nargs="+", required=True, help="Monitor id(s).")
    p.set_defaults(func=_cmd_monitors)

    # nodes
    p = add("nodes", help="List honeydb-agent nodes (last 3 days).")
    p.add_argument("--mydata", action="store_true", help="Only your nodes.")
    p.set_defaults(func=_cmd_nodes)

    # payload-history
    p = add("payload-history", help="Query payload history data.")
    psub = p.add_subparsers(dest="action", metavar="<action>", required=True)

    def padd(name: str, **kwargs: Any) -> argparse.ArgumentParser:
        return psub.add_parser(name, parents=[common], **kwargs)

    padd("remote-hosts", help="Remote hosts grouped by year.")
    pa = padd("attributes", help="List attributes, or one attribute.")
    pa.add_argument("--attribute", help="Group historical data by this attribute.")
    py = padd("year", help="[deprecated] Payload data by year/month.")
    py.add_argument("year", type=int, help="Year, e.g. 2024.")
    py.add_argument("month", type=int, nargs="?", help="Optional month (1-12).")
    padd("services", help="[deprecated] Services with payload data.")
    ps = padd("service", help="[deprecated] Payload data by service.")
    ps.add_argument("name", help="Service name.")
    ph = padd("hash", help="[deprecated] Payload data by hash.")
    ph.add_argument("value", help="Payload hash.")
    p.set_defaults(func=_cmd_payload_history)

    # internet-scanner
    p = add("internet-scanner", help="Check if an IP is a scanner.")
    p.add_argument("ip_address", help="IP address to look up.")
    p.add_argument(
        "--info", action="store_true", help="Include details about the scanner."
    )
    p.set_defaults(func=_cmd_internet_scanner)

    # ipinfo
    p = add("ipinfo", help="Check an IP against known IP lists.")
    p.add_argument("ip_address", help="IP address to look up.")
    p.add_argument(
        "--source",
        choices=IPINFO_SOURCES,
        help="Check a single IP list instead of all.",
    )
    p.set_defaults(func=_cmd_ipinfo)

    # netinfo
    p = add("netinfo", help="Network info lookups (do not count against limits).")
    p.add_argument(
        "action",
        choices=(
            "lookup",
            "network-addresses",
            "prefixes",
            "as-name",
            "geolocation",
        ),
        help="Lookup type.",
    )
    p.add_argument("value", help="IP, CIDR or ASN depending on the lookup type.")
    p.set_defaults(func=_cmd_netinfo)

    # datacenter
    p = add("datacenter", help="Get datacenter/cloud IP ranges.")
    p.add_argument("provider", choices=DATACENTER_PROVIDERS, help="Cloud provider.")
    p.set_defaults(func=_cmd_datacenter)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not getattr(args, "func", None):
        parser.print_help()
        return 2

    api_id = getattr(args, "api_id", None) or os.environ.get("HONEYDB_API_ID")
    api_key = getattr(args, "api_key", None) or os.environ.get("HONEYDB_API_KEY")
    pretty = getattr(args, "pretty", False)
    timeout = getattr(args, "timeout", 30.0)

    if not api_id or not api_key:
        parser.error(
            "API credentials required: set HONEYDB_API_ID and HONEYDB_API_KEY "
            "environment variables, or pass --api-id and --api-key."
        )

    try:
        with Client(api_id, api_key, timeout=timeout) as client:
            result = args.func(client, args)
    except HoneyDBError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    emit(result, pretty)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
