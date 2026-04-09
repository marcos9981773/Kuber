"""
kuber/utils/network.py
Connectivity checks — no PyQt5 imports.
"""
from __future__ import annotations

import logging
import socket

import requests

from kuber.constants import (
    CONNECTIVITY_CHECK_TIMEOUT,
    CONNECTIVITY_CHECK_URL,
    HTTP_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)


def is_internet_available(
    url: str = CONNECTIVITY_CHECK_URL,
    timeout: int = CONNECTIVITY_CHECK_TIMEOUT,
) -> bool:
    """
    Check whether an internet connection is available.

    Performs an HTTP HEAD request to ``url``.  Falls back to a DNS
    lookup of ``google.com`` if the HTTP request fails.

    Args:
        url:     URL to probe (default: Google DNS over HTTP).
        timeout: Request timeout in seconds.

    Returns:
        ``True`` if the internet appears reachable, ``False`` otherwise.
    """
    try:
        response = requests.head(url, timeout=timeout)
        return response.status_code < 500
    except requests.RequestException:
        pass

    # DNS fallback
    try:
        socket.setdefaulttimeout(timeout)
        socket.getaddrinfo("google.com", 80)
        return True
    except OSError:
        logger.warning("Internet connectivity check failed (both HTTP and DNS).")
        return False


def check_host_reachable(host: str, port: int = 443, timeout: int = HTTP_TIMEOUT_SECONDS) -> bool:
    """
    Check whether a specific host:port is reachable via TCP.

    Args:
        host:    Hostname or IP address.
        port:    TCP port to probe.
        timeout: Connection timeout in seconds.

    Returns:
        ``True`` if the connection succeeds, ``False`` otherwise.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError as exc:
        logger.debug(f"Host {host}:{port} not reachable: {exc}")
        return False


def parse_host_port(server_url: str) -> tuple[str, int]:
    """
    Extract hostname and port from a server URL string.

    Args:
        server_url: URL such as ``https://my-cluster.example.com:6443``

    Returns:
        Tuple of (hostname, port).

    Raises:
        ValueError: If the URL cannot be parsed.
    """
    from urllib.parse import urlparse

    parsed = urlparse(server_url)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    if not host:
        raise ValueError(f"Cannot parse host from URL: {server_url!r}")

    return host, port

