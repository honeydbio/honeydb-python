"""HoneyDB — Python API wrapper and CLI for the HoneyDB API.

See https://honeydb.io for more information.
"""

from honeydb.api.client import (
    ASN_RISK_SCANNERS,
    BAD_HOSTS_FORMATS,
    DATACENTER_PROVIDERS,
    IPINFO_SOURCES,
    Client,
)
from honeydb.exceptions import (
    HoneyDBAuthError,
    HoneyDBError,
    HoneyDBNotFoundError,
    HoneyDBRateLimitError,
)

__version__ = "2.2.0"

__all__ = [
    "Client",
    "ASN_RISK_SCANNERS",
    "BAD_HOSTS_FORMATS",
    "DATACENTER_PROVIDERS",
    "IPINFO_SOURCES",
    "HoneyDBError",
    "HoneyDBAuthError",
    "HoneyDBNotFoundError",
    "HoneyDBRateLimitError",
    "__version__",
]
