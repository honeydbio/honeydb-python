"""HoneyDB API client.

A thin, typed wrapper around the HoneyDB REST API (https://honeydb.io).
Requests are made over a pooled :class:`requests.Session` with automatic
retries on transient failures.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from honeydb.exceptions import (
    HoneyDBAuthError,
    HoneyDBError,
    HoneyDBNotFoundError,
    HoneyDBRateLimitError,
)

__all__ = ["Client", "DATACENTER_PROVIDERS", "IPINFO_SOURCES"]

#: IP list sources supported by the ``/ipinfo/<source>`` endpoints.
IPINFO_SOURCES: tuple[str, ...] = (
    "bogon",
    "tor",
    "sansip",
    "ciarmy",
    "et-compromised",
    "project-honeypot",
    "pallebone",
    "threatfox",
    "blocklist_net_ua",
)

#: Datacenter/cloud providers supported by the ``/datacenter/<provider>`` endpoint.
DATACENTER_PROVIDERS: tuple[str, ...] = (
    "aws",
    "azure",
    "azure/china",
    "azure/germany",
    "azure/gov",
    "cloudflare",
    "gcp",
    "ibm",
    "oracle",
)

JSON = Any


class Client:
    """Client for the HoneyDB API.

    Args:
        api_id: Your HoneyDB API ID.
        api_key: Your HoneyDB API key.
        timeout: Per-request timeout in seconds.
        base_url: Base URL of the API (override for testing/proxies).
        session: An existing :class:`requests.Session` to reuse. If omitted, a
            pooled session with retries is created and owned by this client.
        retries: Number of automatic retries for transient errors (429/5xx).

    Example:
        >>> from honeydb import Client
        >>> with Client("api_id", "api_key") as honeydb:
        ...     hosts = honeydb.bad_hosts()
    """

    DEFAULT_BASE_URL = "https://honeydb.io/api"

    def __init__(
        self,
        api_id: str,
        api_key: str,
        *,
        timeout: float = 30.0,
        base_url: str = DEFAULT_BASE_URL,
        session: requests.Session | None = None,
        retries: int = 3,
    ) -> None:
        self.api_id = api_id
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = base_url.rstrip("/")

        self._owns_session = session is None
        self.session = session or self._build_session(retries)
        self.session.headers.update(
            {
                "X-HoneyDb-ApiId": self.api_id,
                "X-HoneyDb-ApiKey": self.api_key,
                "Accept": "application/json",
            }
        )

    # -- infrastructure ---------------------------------------------------

    @staticmethod
    def _build_session(retries: int) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=retries,
            connect=retries,
            read=retries,
            status=retries,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET", "PUT", "DELETE"}),
            respect_retry_after_header=True,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
    ) -> JSON:
        """Send a request and return the parsed JSON body.

        Raises:
            HoneyDBAuthError: On HTTP 401/403.
            HoneyDBNotFoundError: On HTTP 404.
            HoneyDBRateLimitError: On HTTP 429.
            HoneyDBError: On any other HTTP or transport error, or an
                unparseable response body.
        """
        url = f"{self.base_url}{path}"
        try:
            response = self.session.request(
                method,
                url,
                params=params,
                json=json,
                timeout=self.timeout,
            )
        except requests.RequestException as error:
            raise HoneyDBError(f"Request to {url} failed: {error}") from error

        self._raise_for_status(response)

        # Some endpoints (e.g. datacenter feeds with no entitlement/data) return
        # an empty or whitespace-only body with a success status; treat as None.
        if not response.content or not response.text.strip():
            return None
        try:
            return response.json()
        except ValueError as error:
            raise HoneyDBError(
                f"Response from {url} was not valid JSON",
                status_code=response.status_code,
                response=response.text,
            ) from error

    @staticmethod
    def _raise_for_status(response: requests.Response) -> None:
        if response.ok:
            return

        status = response.status_code
        body = response.text
        message = f"HoneyDB API returned HTTP {status}: {body[:200]}"

        if status in (401, 403):
            raise HoneyDBAuthError(message, status_code=status, response=body)
        if status == 404:
            raise HoneyDBNotFoundError(message, status_code=status, response=body)
        if status == 429:
            retry_after = response.headers.get("Retry-After")
            raise HoneyDBRateLimitError(
                message,
                status_code=status,
                response=body,
                retry_after=float(retry_after) if retry_after else None,
            )
        raise HoneyDBError(message, status_code=status, response=body)

    @staticmethod
    def _seg(value: Any) -> str:
        """URL-encode a single path segment."""
        return quote(str(value), safe="")

    # -- lifecycle --------------------------------------------------------

    def close(self) -> None:
        """Close the underlying session if this client owns it."""
        if self._owns_session:
            self.session.close()

    def __enter__(self) -> Client:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    # -- bad hosts --------------------------------------------------------

    def bad_hosts(self, mydata: bool = False) -> JSON:
        """Return bad hosts seen in the last 24 hours.

        Args:
            mydata: If ``True``, return only data from sensors you operate.
        """
        path = "/bad-hosts/mydata" if mydata else "/bad-hosts"
        return self._request("GET", path)

    def bad_hosts_by_service(self, service: str, mydata: bool = False) -> JSON:
        """Return bad hosts for a given service (last 24 hours).

        Args:
            service: Service/protocol name to filter on.
            mydata: If ``True``, return only data from sensors you operate.
        """
        path = f"/bad-hosts/{self._seg(service)}"
        if mydata:
            path += "/mydata"
        return self._request("GET", path)

    # -- ip context -------------------------------------------------------

    def ip(self, ip_address: str) -> JSON:
        """Return full context for an IP (netinfo, threat, history, scanner...)."""
        return self._request("GET", f"/ip/{self._seg(ip_address)}")

    def ip_geo(self, ip_address: str) -> JSON:
        """Return geolocation information for an IP."""
        return self._request("GET", f"/ip/{self._seg(ip_address)}/geo")

    def ip_netinfo(self, ip_address: str) -> JSON:
        """Return AS number, organization and location data for an IP."""
        return self._request("GET", f"/ip/{self._seg(ip_address)}/netinfo")

    def ip_threatinfo(self, ip_address: str) -> JSON:
        """Return threat intel information for an IP."""
        return self._request("GET", f"/ip/{self._seg(ip_address)}/threatinfo")

    def ip_internet_scanner(self, ip_address: str) -> JSON:
        """Return whether an IP is a known internet scanner."""
        return self._request("GET", f"/ip/{self._seg(ip_address)}/internet-scanner")

    def ip_history(self, ip_address: str) -> JSON:
        """Return history of an IP's interactions with the HoneyDB network."""
        return self._request("GET", f"/ip/{self._seg(ip_address)}/history")

    def ip_cve(self, ip_address: str) -> JSON:
        """Return CVEs observed from an IP."""
        return self._request("GET", f"/ip/{self._seg(ip_address)}/cve")

    def ip_cidr(self, cidr: str) -> JSON:
        """Return all IP addresses within a network range (CIDR)."""
        return self._request("GET", f"/ip/cidr/{self._seg(cidr)}")

    # -- asn --------------------------------------------------------------

    def asn(self, as_number: int | str) -> JSON:
        """Return AS number and organization name. Does not count against limits."""
        return self._request("GET", f"/asn/{self._seg(as_number)}")

    def asn_prefixes(self, as_number: int | str) -> JSON:
        """Return IP prefixes for an ASN. Does not count against limits."""
        return self._request("GET", f"/asn/{self._seg(as_number)}/prefixes")

    def asns(self) -> JSON:
        """Return ASNs that interacted with the network in the previous day."""
        return self._request("GET", "/asns")

    def asns_7d(self) -> JSON:
        """Return ASNs that interacted with the network in the last 7 days."""
        return self._request("GET", "/asns-7d")

    # -- cve --------------------------------------------------------------

    def cve(self, cve: str) -> JSON:
        """Return IP history for a given CVE."""
        return self._request("GET", f"/cve/{self._seg(cve)}")

    def cve_ip(self, ip_address: str) -> JSON:
        """Return CVE history for a given IP address."""
        return self._request("GET", f"/cve/ip/{self._seg(ip_address)}")

    # -- sensor data ------------------------------------------------------

    def sensor_data(
        self,
        sensor_data_date: str,
        from_id: int | str | None = None,
        mydata: bool = True,
    ) -> JSON:
        """Return sensor event data for a given date.

        Args:
            sensor_data_date: Date in ``YYYY-MM-DD`` format.
            from_id: Continue retrieving records after this event id (paging).
            mydata: If ``True`` (default), return only data from your sensors.
        """
        path = "/sensor-data/mydata" if mydata else "/sensor-data"
        params: dict[str, Any] = {"sensor-data-date": sensor_data_date}
        if from_id is not None:
            params["from-id"] = from_id
        return self._request("GET", path, params=params)

    def sensor_data_count(self, sensor_data_date: str, mydata: bool = True) -> JSON:
        """Return a count of sensor event data for a given date.

        Args:
            sensor_data_date: Date in ``YYYY-MM-DD`` format.
            mydata: If ``True`` (default), count only data from your sensors.
        """
        path = "/sensor-data/count/mydata" if mydata else "/sensor-data/count"
        return self._request("GET", path, params={"sensor-data-date": sensor_data_date})

    # -- services / stats -------------------------------------------------

    def services(self) -> JSON:
        """Return the network services (protocols) emulated by sensors."""
        return self._request("GET", "/services")

    def stats(self, year: int, month: int) -> JSON:
        """Return summary stats for a given year and month."""
        return self._request("GET", "/stats", params={"year": year, "month": month})

    # -- monitors ---------------------------------------------------------

    def monitors(self) -> JSON:
        """Return the list of current monitors."""
        return self._request("GET", "/monitors")

    def create_monitors(self, monitors: list[dict[str, Any]]) -> JSON:
        """Create one or more monitors.

        Args:
            monitors: A list of monitor definitions. Each is a dict such as
                ``{"monitor_type": "ip_address", "ip_address": "1.2.3.4",
                "description": "..."}``. Supported ``monitor_type`` values include
                ``ip_address``, ``ip_range``, ``asn`` and ``string``.
        """
        return self._request("PUT", "/monitors", json=monitors)

    def delete_monitors(self, ids: list[int]) -> JSON:
        """Delete monitors by id.

        Args:
            ids: List of monitor ids to delete.
        """
        return self._request("DELETE", "/monitors", json={"ids": ids})

    def monitors_logs(self) -> JSON:
        """Return all monitor logs."""
        return self._request("GET", "/monitors/logs")

    def monitors_notifications(self) -> JSON:
        """Return the list of configured monitor notifications."""
        return self._request("GET", "/monitors/notifications")

    # -- nodes ------------------------------------------------------------

    def nodes(self, mydata: bool = False) -> JSON:
        """Return honeydb-agent nodes seen in the last 3 days.

        Args:
            mydata: If ``True``, return only your nodes.
        """
        path = "/nodes/mydata" if mydata else "/nodes"
        return self._request("GET", path)

    # -- payload history --------------------------------------------------

    def payload_history_remote_hosts(self) -> JSON:
        """Return remote hosts from which payload data was extracted, by year."""
        return self._request("GET", "/payload-history/remote-hosts")

    def payload_history_attributes(self) -> JSON:
        """Return the list of attributes extracted from payload data."""
        return self._request("GET", "/payload-history/attributes")

    def payload_history_attribute(self, attribute: str) -> JSON:
        """Return historical payload data grouped by the given attribute."""
        return self._request(
            "GET", f"/payload-history/attributes/{self._seg(attribute)}"
        )

    def payload_history(self, year: int, month: int | None = None) -> JSON:
        """Return payload data for a year (and optional month).

        .. deprecated::
            This endpoint is deprecated by the HoneyDB API and may be removed.
        """
        path = f"/payload-history/{self._seg(year)}"
        if month is not None:
            path += f"/{self._seg(month)}"
        return self._request("GET", path)

    def payload_history_services(self) -> JSON:
        """Return services from which payload data was extracted.

        .. deprecated:: Deprecated by the HoneyDB API.
        """
        return self._request("GET", "/payload-history/services")

    def payload_history_service(self, service: str) -> JSON:
        """Return payload data for a given service.

        .. deprecated:: Deprecated by the HoneyDB API.
        """
        return self._request("GET", f"/payload-history/{self._seg(service)}")

    def payload_history_hash(self, hash: str) -> JSON:
        """Return payload data for a given hash.

        .. deprecated:: Deprecated by the HoneyDB API.
        """
        return self._request("GET", f"/payload-history/{self._seg(hash)}")

    def payload_history_hash_remote_hosts(self, hash: str, year: int) -> JSON:
        """Return remote hosts for a given hash and year.

        .. deprecated:: Deprecated by the HoneyDB API.
        """
        return self._request(
            "GET",
            f"/payload-history/{self._seg(hash)}/remote-hosts/{self._seg(year)}",
        )

    def payload_history_remote_host(self, remote_host: str) -> JSON:
        """Return payload data hashes for a given remote host.

        .. deprecated:: Deprecated by the HoneyDB API.
        """
        return self._request(
            "GET", f"/payload-history/remote-hosts/{self._seg(remote_host)}"
        )

    # -- internet scanner -------------------------------------------------

    def internet_scanner(self, ip_address: str) -> JSON:
        """Return whether an IP is part of a known internet scanning service."""
        return self._request("GET", f"/internet-scanner/{self._seg(ip_address)}")

    def internet_scanner_info(self, ip_address: str) -> JSON:
        """Return internet-scanner status plus details about the scanning entity."""
        return self._request("GET", f"/internet-scanner/info/{self._seg(ip_address)}")

    # -- ipinfo -----------------------------------------------------------

    def ipinfo(self, ip_address: str) -> JSON:
        """Return whether an IP is present on any of the known IP lists."""
        return self._request("GET", f"/ipinfo/{self._seg(ip_address)}")

    def ipinfo_source(self, source: str, ip_address: str) -> JSON:
        """Return whether an IP is present on a specific IP list.

        Args:
            source: One of :data:`IPINFO_SOURCES` (e.g. ``"tor"``, ``"bogon"``).
            ip_address: The IP address to look up.

        Raises:
            ValueError: If ``source`` is not a recognized IP list.
        """
        if source not in IPINFO_SOURCES:
            raise ValueError(
                f"Unknown ipinfo source {source!r}; "
                f"expected one of {', '.join(IPINFO_SOURCES)}"
            )
        return self._request(
            "GET", f"/ipinfo/{self._seg(source)}/{self._seg(ip_address)}"
        )

    # -- netinfo (no monthly limit) --------------------------------------

    def netinfo_lookup(self, ip_address: str) -> JSON:
        """Return AS, network info and geolocation for an IP. No monthly limit."""
        return self._request("GET", f"/netinfo/lookup/{self._seg(ip_address)}")

    def netinfo_network_addresses(self, cidr: str) -> JSON:
        """Return all IP addresses within a network range. No monthly limit."""
        return self._request("GET", f"/netinfo/network-addresses/{self._seg(cidr)}")

    def netinfo_prefixes(self, asn: int | str) -> JSON:
        """Return all prefixes advertised for an AS network. No monthly limit."""
        return self._request("GET", f"/netinfo/prefixes/{self._seg(asn)}")

    def netinfo_as_name(self, asn: int | str) -> JSON:
        """Return the name of an AS network. No monthly limit."""
        return self._request("GET", f"/netinfo/as-name/{self._seg(asn)}")

    def netinfo_geolocation(self, ip_address: str) -> JSON:
        """Return geolocation information for an IP. No monthly limit."""
        return self._request("GET", f"/netinfo/geolocation/{self._seg(ip_address)}")

    # -- datacenter -------------------------------------------------------

    def datacenter(self, provider: str) -> JSON:
        """Return datacenter/cloud IP ranges for a provider. No monthly limit.

        Args:
            provider: One of :data:`DATACENTER_PROVIDERS` (e.g. ``"aws"``,
                ``"gcp"``, ``"azure/china"``).

        Raises:
            ValueError: If ``provider`` is not recognized.
        """
        if provider not in DATACENTER_PROVIDERS:
            raise ValueError(
                f"Unknown datacenter provider {provider!r}; "
                f"expected one of {', '.join(DATACENTER_PROVIDERS)}"
            )
        # provider may contain a sub-path (e.g. "azure/china"); keep the slash.
        return self._request("GET", f"/datacenter/{provider}")
