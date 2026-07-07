"""Tests for the HoneyDB CLI."""

from __future__ import annotations

import json

import pytest

from honeydb import cli

BASE = "https://honeydb.io/api"
CREDS = ["--api-id", "id", "--api-key", "key"]


def run(argv, requests_mock=None):
    return cli.main([*CREDS, *argv])


def test_no_command_prints_help(capsys):
    assert cli.main([]) == 2
    out = capsys.readouterr().out
    assert "usage:" in out


def test_missing_credentials_errors(monkeypatch):
    monkeypatch.delenv("HONEYDB_API_ID", raising=False)
    monkeypatch.delenv("HONEYDB_API_KEY", raising=False)
    with pytest.raises(SystemExit):
        cli.main(["services"])


def test_services_command(capsys, requests_mock):
    requests_mock.get(f"{BASE}/services", json=["ssh", "http"])
    assert run(["services"]) == 0
    assert json.loads(capsys.readouterr().out) == ["ssh", "http"]


def test_pretty_output(capsys, requests_mock):
    requests_mock.get(f"{BASE}/services", json=["ssh"])
    run(["--pretty", "services"])
    assert "\n" in capsys.readouterr().out.strip()


def test_ip_view_flag(capsys, requests_mock):
    m = requests_mock.get(f"{BASE}/ip/8.8.8.8/geo", json={"country": "US"})
    run(["ip", "8.8.8.8", "--geo"])
    assert m.last_request.path == "/api/ip/8.8.8.8/geo"


def test_ip_default_full_context(requests_mock):
    m = requests_mock.get(f"{BASE}/ip/8.8.8.8", json={})
    run(["ip", "8.8.8.8"])
    assert m.last_request.path == "/api/ip/8.8.8.8"


def test_asns_days_7(requests_mock):
    m = requests_mock.get(f"{BASE}/asns-7d", json=[])
    run(["asns", "--days", "7"])
    assert m.last_request.path == "/api/asns-7d"


def test_asn_prefixes(requests_mock):
    m = requests_mock.get(f"{BASE}/asn/15169/prefixes", json=[])
    run(["asn", "15169", "--prefixes"])
    assert m.last_request.path == "/api/asn/15169/prefixes"


def test_monitors_list(requests_mock):
    m = requests_mock.get(f"{BASE}/monitors", json=[])
    run(["monitors", "list"])
    assert m.last_request.path == "/api/monitors"


def test_global_flag_after_nested_subcommand(capsys, requests_mock):
    # --pretty must be accepted after a nested subcommand action too.
    requests_mock.get(f"{BASE}/monitors", json=[{"id": 1}])
    assert run(["monitors", "list", "--pretty"]) == 0
    assert "\n" in capsys.readouterr().out.strip()


def test_monitors_create_inline_json(requests_mock):
    m = requests_mock.put(f"{BASE}/monitors", json={"ok": True})
    run(["monitors", "create", "--json", '{"monitor_type": "asn"}'])
    assert m.last_request.json() == [{"monitor_type": "asn"}]


def test_monitors_delete(requests_mock):
    m = requests_mock.delete(f"{BASE}/monitors", json={})
    run(["monitors", "delete", "--id", "1", "2"])
    assert m.last_request.json() == {"ids": [1, 2]}


def test_ipinfo_source(requests_mock):
    m = requests_mock.get(f"{BASE}/ipinfo/tor/1.2.3.4", json={})
    run(["ipinfo", "1.2.3.4", "--source", "tor"])
    assert m.last_request.path == "/api/ipinfo/tor/1.2.3.4"


def test_datacenter(requests_mock):
    m = requests_mock.get(f"{BASE}/datacenter/aws", json=[])
    run(["datacenter", "aws"])
    assert m.last_request.path == "/api/datacenter/aws"


def test_netinfo_lookup(requests_mock):
    m = requests_mock.get(f"{BASE}/netinfo/lookup/1.2.3.4", json={})
    run(["netinfo", "lookup", "1.2.3.4"])
    assert m.last_request.path == "/api/netinfo/lookup/1.2.3.4"


def test_sensor_data_count(requests_mock):
    m = requests_mock.get(f"{BASE}/sensor-data/count/mydata", json={"count": 1})
    run(["sensor-data", "--date", "2025-04-01", "--count"])
    assert m.last_request.qs["sensor-data-date"] == ["2025-04-01"]


def test_api_error_returns_1(capsys, requests_mock):
    requests_mock.get(f"{BASE}/services", status_code=401, text="denied")
    assert run(["services"]) == 1
    assert "error:" in capsys.readouterr().err


def test_global_flags_after_subcommand(capsys, requests_mock):
    # --pretty / credentials must work when given after the subcommand too.
    requests_mock.get(f"{BASE}/services", json=["ssh"])
    assert cli.main(["services", "--api-id", "id", "--api-key", "key", "--pretty"]) == 0
    assert "\n" in capsys.readouterr().out.strip()


def test_env_credentials(monkeypatch, requests_mock):
    monkeypatch.setenv("HONEYDB_API_ID", "envid")
    monkeypatch.setenv("HONEYDB_API_KEY", "envkey")
    m = requests_mock.get(f"{BASE}/services", json=[])
    assert cli.main(["services"]) == 0
    assert m.last_request.headers["X-HoneyDb-ApiId"] == "envid"
