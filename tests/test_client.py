"""Tests for the HoneyDB API client using mocked HTTP responses."""

from __future__ import annotations

import pytest

from honeydb import (
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
