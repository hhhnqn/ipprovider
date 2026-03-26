"""Detección de direcciones IPv4 e IPv6 en texto."""

from __future__ import annotations

import ipaddress
import re
import string
from typing import Iterator

_HEX = frozenset(string.hexdigits)

# IPv4 estándar
_IPV4_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
    r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
)

_CHUNK_RE = re.compile(r"^[0-9A-Fa-f:.]+$")


def _parse_ip(s: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(s)
    except ValueError:
        return None


def _longest_ipv6_from(text: str, start: int) -> tuple[int, ipaddress.IPv6Address] | None:
    """Toma la subcadena más larga desde `start` que sea una IPv6 válida."""
    max_end = min(len(text), start + 50)
    best_end: int | None = None
    best_ip: ipaddress.IPv6Address | None = None
    for e in range(start + 2, max_end + 1):
        chunk = text[start:e]
        if not _CHUNK_RE.match(chunk):
            break
        ip = _parse_ip(chunk)
        if isinstance(ip, ipaddress.IPv6Address):
            best_end = e
            best_ip = ip
    if best_end is None or best_ip is None:
        return None
    return best_end, best_ip


def _iter_ipv6_spans(text: str) -> Iterator[tuple[int, int, ipaddress.IPv6Address]]:
    n = len(text)
    i = 0
    while i < n:
        c = text[i]
        if c not in _HEX and c != ":":
            i += 1
            continue
        span = _longest_ipv6_from(text, i)
        if span is None:
            i += 1
            continue
        end, ip = span
        yield i, end, ip
        i = end


def _ipv4_overlaps_span(a: int, b: int, ipv6_spans: list[tuple[int, int]]) -> bool:
    for s, e in ipv6_spans:
        if a < e and s < b:
            return True
    return False


def _normalize(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> str:
    return ip.compressed if isinstance(ip, ipaddress.IPv6Address) else str(ip)


def find_ips_in_text(text: str) -> list[str]:
    """
    Devuelve direcciones IP únicas en orden de primera aparición en el texto.
    """
    ipv6_spans: list[tuple[int, int]] = []
    matches: list[tuple[int, str]] = []
    seen: set[str] = set()

    for start, end, ip in _iter_ipv6_spans(text):
        ipv6_spans.append((start, end))
        norm = _normalize(ip)
        if norm not in seen:
            seen.add(norm)
            matches.append((start, norm))

    for m in _IPV4_RE.finditer(text):
        s = m.group(0)
        a, b = m.start(), m.end()
        if _ipv4_overlaps_span(a, b, ipv6_spans):
            continue
        ip = _parse_ip(s)
        if ip is None or not isinstance(ip, ipaddress.IPv4Address):
            continue
        norm = _normalize(ip)
        if norm not in seen:
            seen.add(norm)
            matches.append((a, norm))

    matches.sort(key=lambda x: x[0])
    return [s for _, s in matches]
