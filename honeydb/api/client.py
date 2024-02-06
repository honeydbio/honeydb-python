"""
HoneyDB API Client
"""

import requests


class Client(object):
    """
    Base class for making requests to the HoneyDB API.
    https://honeydb.io/#threats
    """

    base_url = "https://honeydb.io/api"

    api_id = None
    api_key = None
    ep_bad_hosts = "/bad-hosts"
    ep_ip_history = "/ip-history"
    ep_payload_history = "/payload-history"
    ep_sensor_data_count = "/sensor-data/count"
    ep_sensor_data = "/sensor-data"
    ep_services = "/services"
    ep_stats = "/stats"
    ep_stats_asn = "/stats/asn"
    ep_twitter_threat_feed = "/twitter-threat-feed"
    ep_nodes = "/nodes"
    ep_netinfo_lookup = "/netinfo/lookup"
    ep_netinfo_network_addresses = "/netinfo/network-addresses"
    ep_netinfo_prefixes = "/netinfo/prefixes"
    ep_netinfo_as_name = "/netinfo/as-name"
    ep_netinfo_geolocation = "/netinfo/geolocation"
    ep_datacenter = "/datacenter"

    def __init__(self, api_id, api_key):
        """
        Return a HoneyDB object
        """
        self.api_id = api_id
        self.api_key = api_key

    def _make_request(self, endpoint, method="GET", options=None):
        """
        Compose and submit API call.
        """
        data = dict()

        headers = {"X-HoneyDb-ApiId": self.api_id, "X-HoneyDb-ApiKey": self.api_key}

        if options is not None:
            for key in options:
                data[key] = options[key]

        url = self.base_url + endpoint
        result = None

        if method == "GET":
            result = requests.get(url, params=data, headers=headers)
        elif method == "POST":
            headers["Content-Type"] = "application/json"
            result = requests.post(url, json=data, headers=headers)
        else:
            raise Exception("InvalidMethod: " + str(method))
        return result.json()

    def bad_hosts(self, service=None, mydata=False):
        """
        Get bad-hosts
        """
        endpoint = self.ep_bad_hosts

        if service is not None:
            endpoint += "/{}".format(service)

        if mydata:
            endpoint += "/mydata"

        return self._make_request(endpoint=endpoint)

    def bad_hosts_service(self, service, mydata=False):
        """
        Get bad-hosts by service
        """
        if mydata:
            endpoint = "{}/{}/mydata".format(service, self.ep_bad_hosts)
        else:
            endpoint = "{}/{}".format(self.ep_bad_hosts, service)

        return self._make_request(endpoint=endpoint)

    def ip_history(self, ip_address: str) -> dict:
        """
        Get IP History for given IP
        """
        endpoint = f"{self.ep_ip_history}/{ip_address}"

        return self._make_request(endpoint=endpoint)

    def payload_history(
        self, year: int = None, month: int = None, hash: str = None
    ) -> dict:
        """
        Get payload history
        """
        if hash:
            endpoint = f"{self.ep_payload_history}/{hash}"

        elif year and month:
            endpoint = f"{self.ep_payload_history}/{year}/{month}"

        elif year:
            endpoint = f"{self.ep_payload_history}/{year}"

        return self._make_request(endpoint=endpoint)

    def payload_history_services(self, service: str = None) -> dict:
        """
        Get payload history services
        """
        endpoint = f"{self.ep_payload_history}/services"

        if service:
            endpoint = f"{self.ep_payload_history}/{service}"

        return self._make_request(endpoint=endpoint)

    def payload_history_remote_hosts(
        self, remote_host: str = None, hash: str = None, year: int = None
    ) -> dict:
        """
        Get payload history remote hosts
        """
        endpoint = f"{self.ep_payload_history}/remote-hosts"

        if hash and year:
            endpoint = f"{self.ep_payload_history}/{hash}/remote-hosts/{year}"

        if remote_host:
            endpoint = f"{self.ep_payload_history}/remote-hosts/{remote_host}"

        return self._make_request(endpoint=endpoint)

    def payload_history_attributes(self, attribute: str = None) -> dict:
        """
        Get payload history attributes
        """
        endpoint = f"{self.ep_payload_history}/attributes"

        if attribute:
            endpoint = f"{endpoint}/{attribute}"

        return self._make_request(endpoint=endpoint)

    def sensor_data_count(self, sensor_data_date=None, mydata=True):
        """
        Get sensor data count
        """
        if mydata:
            endpoint = "{}/mydata".format(self.ep_sensor_data_count)
        else:
            endpoint = self.ep_sensor_data_count

        if sensor_data_date is not None:
            endpoint = "{}?sensor-data-date={}".format(endpoint, sensor_data_date)
        else:
            raise Exception("MissingParameter: sensor_data_date")

        return self._make_request(endpoint=endpoint)

    def sensor_data(self, sensor_data_date=None, from_id=None, mydata=True):
        """
        Get sensor data
        """
        if mydata:
            endpoint = "{}/mydata".format(self.ep_sensor_data)
        else:
            endpoint = self.ep_sensor_data

        if sensor_data_date is not None:
            endpoint = "{}?sensor-data-date={}".format(endpoint, sensor_data_date)

            if from_id is not None:
                endpoint = "{}&from-id={}".format(endpoint, from_id)

        return self._make_request(endpoint=endpoint)

    def services(self):
        """
        Get services
        """
        endpoint = self.ep_services

        return self._make_request(endpoint=endpoint)

    def stats(self, year: int, month: int) -> dict:
        """
        Get stats
        """
        endpoint = f"{self.ep_stats}?year={year}&month={month}"

        return self._make_request(endpoint=endpoint)

    def stats_asn(self) -> dict:
        """
        Get stats-asn
        """
        return self._make_request(endpoint=self.ep_stats_asn)

    def twitter_threat_feed(self, ipaddress=None):
        """
        Get twitter threat feed
        """
        if ipaddress is not None:
            endpoint = "{}/{}".format(self.ep_twitter_threat_feed, ipaddress)
        else:
            endpoint = self.ep_twitter_threat_feed

        return self._make_request(endpoint=endpoint)

    def nodes(self, mydata=False):
        """
        Get nodes
        """
        if mydata:
            endpoint = "{}/mydata".format(self.ep_nodes)
        else:
            endpoint = self.ep_nodes

        return self._make_request(endpoint=endpoint)

    def netinfo_lookup(self, ipaddress):
        """
        Get netinfo for given ipaddress
        """
        endpoint = "{}/{}".format(self.ep_netinfo_lookup, ipaddress)
        return self._make_request(endpoint=endpoint)

    def netinfo_network_addresses(self, cidr):
        """
        Get network addresses for given cidr
        """
        endpoint = "{}/{}".format(self.ep_netinfo_network_addresses, cidr)
        return self._make_request(endpoint=endpoint)

    def netinfo_prefixes(self, asn):
        """
        Get prefixes for given asn
        """
        endpoint = "{}/{}".format(self.ep_netinfo_prefixes, asn)
        return self._make_request(endpoint=endpoint)

    def netinfo_as_name(self, asn):
        """
        Get AS name for given asn
        """
        endpoint = "{}/{}".format(self.ep_netinfo_as_name, asn)
        return self._make_request(endpoint=endpoint)

    def netinfo_geolocation(self, ipaddress):
        """
        Get GEO location for given ipaddress
        """
        endpoint = "{}/{}".format(self.ep_netinfo_geolocation, ipaddress)
        return self._make_request(endpoint=endpoint)

    def datacenter(self, datacenter: str) -> dict:
        """
        Get datacenter ip ranges
        """
        endpoint = f"{self.ep_datacenter}/{datacenter}"
        return self._make_request(endpoint=endpoint)
