"""Tests for the HoneyDB API client using mocked HTTP responses."""

from __future__ import annotations

import pytest

from honeydb import (
    ASN_RISK_SCANNERS,
    Client,
    HoneyDBAuthError,
    HoneyDBError,
    HoneyDBNotFoundError,
    HoneyDBRateLimitError,
)

BASE = "https://honeydb.io/api"


@pytest.fixture
def client():
    with Client("test-id", "test-key") as c:
        yield c


def test_auth_headers_are_sent(client, requests_mock):
    m = requests_mock.get(f"{BASE}/services", json=["ssh"])
    client.services()
    assert m.last_request.headers["X-HoneyDb-ApiId"] == "test-id"
    assert m.last_request.headers["X-HoneyDb-ApiKey"] == "test-key"


def test_bad_hosts(client, requests_mock):
    requests_mock.get(f"{BASE}/bad-hosts", json=[{"remote_host": "1.2.3.4"}])
    assert client.bad_hosts() == [{"remote_host": "1.2.3.4"}]


def test_bad_hosts_mydata(client, requests_mock):
    requests_mock.get(f"{BASE}/bad-hosts/mydata", json=[])
    assert client.bad_hosts(mydata=True) == []


def test_bad_hosts_by_service_mydata(client, requests_mock):
    m = requests_mock.get(f"{BASE}/bad-hosts/ssh/mydata", json=[])
    client.bad_hosts_by_service("ssh", mydata=True)
    assert m.last_request.path == "/api/bad-hosts/ssh/mydata"


def test_ip_full_context(client, requests_mock):
    requests_mock.get(f"{BASE}/ip/8.8.8.8", json={"ip": "8.8.8.8"})
    assert client.ip("8.8.8.8") == {"ip": "8.8.8.8"}


def test_ip_history(client, requests_mock):
    m = requests_mock.get(f"{BASE}/ip/8.8.8.8/history", json=[])
    client.ip_history("8.8.8.8")
    assert m.last_request.path == "/api/ip/8.8.8.8/history"


def test_ip_cidr(client, requests_mock):
    m = requests_mock.get(f"{BASE}/ip/cidr/1.2.3.0%2F24", json=[])
    client.ip_cidr("1.2.3.0/24")
    # the slash within the CIDR segment is percent-encoded so it is not
    # mistaken for a path separator
    assert m.last_request.path.lower() == "/api/ip/cidr/1.2.3.0%2f24"


def test_sensor_data_params(client, requests_mock):
    m = requests_mock.get(f"{BASE}/sensor-data/mydata", json=[])
    client.sensor_data("2025-04-01", from_id=123)
    assert m.last_request.qs["sensor-data-date"] == ["2025-04-01"]
    assert m.last_request.qs["from-id"] == ["123"]


def test_sensor_data_count_all(client, requests_mock):
    m = requests_mock.get(f"{BASE}/sensor-data/count", json={"count": 0})
    client.sensor_data_count("2025-04-01", mydata=False)
    assert m.last_request.path == "/api/sensor-data/count"


def test_stats_params(client, requests_mock):
    m = requests_mock.get(f"{BASE}/stats", json={})
    client.stats(2024, 1)
    assert m.last_request.qs == {"year": ["2024"], "month": ["1"]}


def test_create_monitors_put_body(client, requests_mock):
    m = requests_mock.put(f"{BASE}/monitors", json={"created": 1})
    payload = [{"monitor_type": "asn", "monitor_value": "401120"}]
    client.create_monitors(payload)
    assert m.last_request.method == "PUT"
    assert m.last_request.json() == payload


def test_delete_monitors_body(client, requests_mock):
    m = requests_mock.delete(f"{BASE}/monitors", json={"deleted": 2})
    client.delete_monitors([122, 123])
    assert m.last_request.method == "DELETE"
    assert m.last_request.json() == {"ids": [122, 123]}


def test_ipinfo_source_valid(client, requests_mock):
    m = requests_mock.get(f"{BASE}/ipinfo/tor/1.2.3.4", json={"tor": True})
    client.ipinfo_source("tor", "1.2.3.4")
    assert m.last_request.path == "/api/ipinfo/tor/1.2.3.4"


def test_ipinfo_source_invalid(client):
    with pytest.raises(ValueError, match="Unknown ipinfo source"):
        client.ipinfo_source("nope", "1.2.3.4")


def test_datacenter_subpath(client, requests_mock):
    m = requests_mock.get(f"{BASE}/datacenter/azure/china", json=[])
    client.datacenter("azure/china")
    assert m.last_request.path == "/api/datacenter/azure/china"


def test_datacenter_invalid(client):
    with pytest.raises(ValueError, match="Unknown datacenter provider"):
        client.datacenter("digitalocean")


def test_netinfo_as_name(client, requests_mock):
    m = requests_mock.get(f"{BASE}/netinfo/as-name/15169", json={"name": "GOOGLE"})
    assert client.netinfo_as_name(15169) == {"name": "GOOGLE"}
    assert m.last_request.path == "/api/netinfo/as-name/15169"


# -- asn risk -------------------------------------------------------------


def test_asn_risk_sends_no_params_by_default(client, requests_mock):
    m = requests_mock.get(f"{BASE}/asn-risk", json={"report_month": "2026-08"})
    client.asn_risk()
    assert m.last_request.path == "/api/asn-risk"
    assert m.last_request.qs == {}


def test_asn_risk_period_only(client, requests_mock):
    m = requests_mock.get(f"{BASE}/asn-risk", json={})
    client.asn_risk(period="2026-07")
    assert m.last_request.qs == {"period": ["2026-07"]}


def test_asn_risk_all_params(client, requests_mock):
    m = requests_mock.get(f"{BASE}/asn-risk", json={})
    client.asn_risk(period="2026-08", limit=250, scanners="exclude")
    assert m.last_request.qs == {
        "period": ["2026-08"],
        "limit": ["250"],
        "scanners": ["exclude"],
    }


def test_asn_risk_limit_all_sentinel(client, requests_mock):
    m = requests_mock.get(f"{BASE}/asn-risk", json={})
    client.asn_risk(limit="all")
    assert m.last_request.qs == {"limit": ["all"]}


def test_asn_risk_limit_int_is_stringified(client, requests_mock):
    m = requests_mock.get(f"{BASE}/asn-risk", json={})
    client.asn_risk(limit=25)
    assert m.last_request.qs == {"limit": ["25"]}


def test_asn_risk_limit_digit_string(client, requests_mock):
    # The CLI hands --limit over as a string; digit-strings must be accepted.
    m = requests_mock.get(f"{BASE}/asn-risk", json={})
    client.asn_risk(limit="25")
    assert m.last_request.qs == {"limit": ["25"]}


@pytest.mark.parametrize("period", ["2026-13", "26-07", "2026-7", "2026", 202607])
def test_asn_risk_invalid_period_makes_no_request(client, requests_mock, period):
    m = requests_mock.get(f"{BASE}/asn-risk", json={})
    with pytest.raises(ValueError, match="Invalid period"):
        client.asn_risk(period=period)
    assert m.call_count == 0


@pytest.mark.parametrize("limit", [0, -1, "0", 100000, "123456", "none"])
def test_asn_risk_invalid_limit_makes_no_request(client, requests_mock, limit):
    m = requests_mock.get(f"{BASE}/asn-risk", json={})
    with pytest.raises(ValueError, match="Invalid limit"):
        client.asn_risk(limit=limit)
    assert m.call_count == 0


def test_asn_risk_bool_limit_rejected(client, requests_mock):
    # bool is a subclass of int; limit=True must not slip through as limit=1.
    m = requests_mock.get(f"{BASE}/asn-risk", json={})
    with pytest.raises(ValueError, match="Invalid limit"):
        client.asn_risk(limit=True)
    assert m.call_count == 0


def test_asn_risk_invalid_scanners(client, requests_mock):
    m = requests_mock.get(f"{BASE}/asn-risk", json={})
    with pytest.raises(ValueError, match="Unknown scanners filter"):
        client.asn_risk(scanners="nope")
    assert m.call_count == 0


def test_asn_risk_no_data_returns_empty_list(client, requests_mock):
    # A month with no report object is a 200 [] -- not a 404, and not an error.
    requests_mock.get(f"{BASE}/asn-risk", json=[])
    assert client.asn_risk(period="2020-01") == []


def test_asn_risk_history_path(client, requests_mock):
    m = requests_mock.get(f"{BASE}/asn/15169/risk", json={"asn": "15169"})
    assert client.asn_risk_history(15169) == {"asn": "15169"}
    assert m.last_request.path == "/api/asn/15169/risk"


def test_asn_risk_history_accepts_string_asn(client, requests_mock):
    m = requests_mock.get(f"{BASE}/asn/15169/risk", json={})
    client.asn_risk_history("15169")
    assert m.last_request.path == "/api/asn/15169/risk"


def test_asn_risk_history_non_numeric_asn_is_not_found(client, requests_mock):
    # A non-numeric ASN misses the router's ^[0-9]{1,10}$ match and gets the
    # branded HTML 404 page rather than JSON.
    requests_mock.get(
        f"{BASE}/asn/abc/risk",
        status_code=404,
        text="<!DOCTYPE html><html><body>Page not found</body></html>",
    )
    with pytest.raises(HoneyDBNotFoundError):
        client.asn_risk_history("abc")


def test_asn_risk_history_no_data_returns_empty_list(client, requests_mock):
    requests_mock.get(f"{BASE}/asn/64512/risk", json=[])
    assert client.asn_risk_history(64512) == []


def test_asn_risk_scanners_exported_from_every_surface():
    import honeydb
    import honeydb.api
    import honeydb.api.client

    for module in (honeydb, honeydb.api, honeydb.api.client):
        assert module.ASN_RISK_SCANNERS == ("exclude", "only", "include")
        assert "ASN_RISK_SCANNERS" in module.__all__
    assert ASN_RISK_SCANNERS == honeydb.api.client.ASN_RISK_SCANNERS


def test_version_matches_package_metadata():
    from importlib.metadata import version

    import honeydb

    assert version("honeydb") == honeydb.__version__


@pytest.mark.parametrize(
    ("status", "exc"),
    [
        (401, HoneyDBAuthError),
        (403, HoneyDBAuthError),
        (404, HoneyDBNotFoundError),
        (429, HoneyDBRateLimitError),
        (500, HoneyDBError),
    ],
)
def test_error_mapping(client, requests_mock, status, exc):
    requests_mock.get(f"{BASE}/services", status_code=status, text="boom")
    with pytest.raises(exc) as info:
        client.services()
    assert info.value.status_code == status


def test_rate_limit_retry_after(client, requests_mock):
    requests_mock.get(
        f"{BASE}/services",
        status_code=429,
        text="slow down",
        headers={"Retry-After": "30"},
    )
    with pytest.raises(HoneyDBRateLimitError) as info:
        client.services()
    assert info.value.retry_after == 30.0


def test_invalid_json_raises(client, requests_mock):
    requests_mock.get(f"{BASE}/services", text="not json")
    with pytest.raises(HoneyDBError, match="not valid JSON"):
        client.services()


def test_empty_body_returns_none(client, requests_mock):
    requests_mock.get(f"{BASE}/services", content=b"")
    assert client.services() is None


def test_whitespace_body_returns_none(client, requests_mock):
    # datacenter feeds can return a whitespace-only body on success.
    requests_mock.get(f"{BASE}/datacenter/aws", text="\n\n")
    assert client.datacenter("aws") is None


def test_provided_session_not_closed():
    import requests

    session = requests.Session()
    client = Client("id", "key", session=session)
    client.close()
    # A session we didn't create must remain usable.
    assert session.adapters  # not closed/cleared by us
