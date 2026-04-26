from __future__ import annotations

import ipaddress
import logging
import os
import re
import socket
import subprocess
from typing import Iterable

LOGGER = logging.getLogger(__name__)

_IPV4_RE = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
_IPV6_RE = re.compile(r"(?<![0-9A-Fa-f:])(?:[0-9A-Fa-f]{0,4}:){2,}[0-9A-Fa-f]{0,4}(?:%\w+)?")


def _is_usable_ip(value: str) -> bool:
    value = value.strip().split("%", 1)[0]
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False
    if ip.is_loopback or ip.is_link_local or ip.is_unspecified or ip.is_multicast:
        return False
    return True


def _collect_socket_addresses() -> set[str]:
    addresses: set[str] = set()
    names = {socket.gethostname(), socket.getfqdn()}
    for name in names:
        if not name:
            continue
        try:
            for family, _type, _proto, _canon, sockaddr in socket.getaddrinfo(name, None):
                if family in (socket.AF_INET, socket.AF_INET6) and sockaddr:
                    addresses.add(str(sockaddr[0]))
        except OSError:
            pass

    # UDP connect does not send packets, but it usually reveals the local address
    # selected for an external route. It is a useful APIPA/offline guard without
    # contacting a web service.
    for family, target in (
        (socket.AF_INET, ("8.8.8.8", 80)),
        (socket.AF_INET6, ("2001:4860:4860::8888", 80)),
    ):
        try:
            with socket.socket(family, socket.SOCK_DGRAM) as sock:
                sock.settimeout(0.25)
                sock.connect(target)
                addresses.add(str(sock.getsockname()[0]))
        except OSError:
            pass
    return addresses


def _collect_command_addresses() -> set[str]:
    commands: list[list[str]] = []
    if os.name == "nt":
        commands.append(["ipconfig"])
    else:
        commands.append(["ip", "-o", "addr", "show"])
        commands.append(["ifconfig"])

    addresses: set[str] = set()
    for cmd in commands:
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True, encoding="utf-8", errors="ignore", timeout=2.5)
        except Exception:
            continue
        for match in _IPV4_RE.findall(output):
            addresses.add(match)
        for match in _IPV6_RE.findall(output):
            addresses.add(match)
    return addresses


def collect_local_ip_addresses() -> list[str]:
    addresses = _collect_socket_addresses() | _collect_command_addresses()
    return sorted(addresses)


def has_normal_network_address(addresses: Iterable[str] | None = None) -> tuple[bool, list[str]]:
    """Return whether the machine has a non-loopback, non-APIPA/link-local IP.

    Private LAN addresses such as 192.168.x.x, 10.x.x.x and fd00::/8 are valid
    here because they indicate that the machine received a normal network config.
    APIPA 169.254.x.x and IPv6 fe80:: link-local addresses are intentionally not
    enough for first-start online preloading.
    """
    values = list(addresses) if addresses is not None else collect_local_ip_addresses()
    usable = [addr for addr in values if _is_usable_ip(addr)]
    LOGGER.debug("Detected local IP addresses: %s; usable=%s", values, usable)
    return bool(usable), usable
