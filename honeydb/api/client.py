"""
HoneyDB API Client
"""

import requests


class Client(object):
    """
    Base class for making requests to the HoneyDB API.
    https://riskdiscovery.com/honeydb/#threats
    """
    base_url = "https://riskdiscovery.com/honeydb/api"

    api_id = None
    api_key = None
    ep_bad_hosts = "/bad-hosts"
    ep_sensor_data_count = "/sensor-data/count"
    ep_sensor_data = "/sensor-data"
    ep_threatbin = "/threatbin"
    ep_twitter_threat_feed = "/twitter-threat-feed"

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

        headers = {
            'X-HoneyDb-ApiId': self.api_id,
            'X-HoneyDb-ApiKey': self.api_key
        }

        if options is not None:
            for key in options:
                data[key] = options[key]

        url = self.base_url + endpoint
        result = None

        if method == "GET":
            result = requests.get(url, params=data, headers=headers)
        elif method == "POST":
            headers['Content-Type'] = "application/json"
            result = requests.post(url, json=data, headers=headers)
        else:
            raise Exception("InvalidMethod: " + str(method))

        return result.json()

    def bad_hosts(self, mydata=False):
        """
        Get bad-hosts
        """
        if mydata:
            endpoint = "{}/mydata".format(self.ep_bad_hosts)
        else:
            endpoint = self.ep_bad_hosts

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
            endpoint = "{}?sensor-data-date={}".format(
                endpoint, sensor_data_date)
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
            endpoint = "{}?sensor-data-date={}".format(
                endpoint, sensor_data_date)

            if from_id is not None:
                endpoint = "{}&from-id={}".format(endpoint, from_id)

        return self._make_request(endpoint=endpoint)

    def threatbin(self):
        """
        Get threatbin
        """
        return self._make_request(endpoint=self.ep_threatbin)

    def twitter_threat_feed(self, ipaddress=None):
        """
        Get twitter threat feed
        """
        if ipaddress is not None:
            endpoint = "{}/{}".format(self.ep_twitter_threat_feed, ipaddress)
        else:
            endpoint = self.ep_twitter_threat_feed

        return self._make_request(endpoint=endpoint)
