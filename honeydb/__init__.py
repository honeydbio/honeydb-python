"""HoneyDB — Python API wrapper and CLI for the HoneyDB API.

See https://honeydb.io for more information.
"""

from honeydb.api.client import (
    ASN_RISK_SCANNERS,
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

__version__ = "2.1.2"

__all__ = [
    "Client",
    "ASN_RISK_SCANNERS",
    "DATACENTER_PROVIDERS",
    "IPINFO_SOURCES",
    "HoneyDBError",
    "HoneyDBAuthError",
    "HoneyDBNotFoundError",
    "HoneyDBRateLimitError",
    "__version__",
]
