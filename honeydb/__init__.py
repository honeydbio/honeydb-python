"""HoneyDB — Python API wrapper and CLI for the HoneyDB API.

See https://honeydb.io for more information.
"""

from honeydb.api.client import DATACENTER_PROVIDERS, IPINFO_SOURCES, Client
from honeydb.exceptions import (
    HoneyDBAuthError,
    HoneyDBError,
    HoneyDBNotFoundError,
    HoneyDBRateLimitError,
)

__version__ = "2.0.0"

__all__ = [
    "Client",
    "DATACENTER_PROVIDERS",
    "IPINFO_SOURCES",
    "HoneyDBError",
    "HoneyDBAuthError",
    "HoneyDBNotFoundError",
    "HoneyDBRateLimitError",
    "__version__",
]
