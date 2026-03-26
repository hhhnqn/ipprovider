"""Enriquecimiento de IPs públicas mediante RDAP (ipwhois)."""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from typing import Any

from ipwhois import IPWhois
from ipwhois.exceptions import BaseIpwhoisException


@dataclass
class IpReportRow:
    """Fila del informe para una dirección."""

    address: str
    ip_version: str
    scope: str
    is_public: bool
    asn: str
    organization: str
    network_cidr: str
    error: str | None = None


def _classify_scope(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> tuple[str, bool]:
    if ip.is_loopback:
        return "loopback", False
    if ip.is_link_local:
        return "enlace local", False
    if ip.is_multicast:
        return "multicast", False
    if ip.is_private:
        return "privada", False
    if ip.is_reserved:
        return "reservada", False
    if ip.is_global:
        return "pública", True
    return "no global", False


def _rdap_to_row(address: str, rdap: dict[str, Any]) -> tuple[str, str, str]:
    asn_raw = rdap.get("asn") or rdap.get("asn_number")
    asn = str(asn_raw).strip() if asn_raw not in (None, "", "NA") else ""

    asn_desc = (rdap.get("asn_description") or "").strip()
    network_obj = rdap.get("network") or {}
    if isinstance(network_obj, dict):
        name = (network_obj.get("name") or "").strip()
        cidr = (network_obj.get("cidr") or "").strip()
    else:
        name, cidr = "", ""

    org = asn_desc or name or ""
    if not org and rdap.get("entities"):
        for ent in rdap["entities"]:
            if isinstance(ent, dict) and ent.get("roles") and "registrant" in ent["roles"]:
                vcard = ent.get("vcard_array")
                if isinstance(vcard, list) and len(vcard) > 1:
                    for item in vcard[1:]:
                        if isinstance(item, list) and len(item) > 3 and item[0] == "fn":
                            org = str(item[3])
                            break
                if org:
                    break

    return asn or "—", org or "—", cidr or "—"


def lookup_rdap(address: str) -> dict[str, Any]:
    """Consulta RDAP para una IP (para tests con mock)."""
    w = IPWhois(address)
    return w.lookup_rdap()


def enrich_ip(
    address: str,
    *,
    lookup_fn=lookup_rdap,
) -> IpReportRow:
    """Construye una fila de informe; solo consulta RDAP si la IP es pública."""
    ip = ipaddress.ip_address(address)
    scope, is_public = _classify_scope(ip)
    ver = "IPv4" if isinstance(ip, ipaddress.IPv4Address) else "IPv6"

    if not is_public:
        return IpReportRow(
            address=address,
            ip_version=ver,
            scope=scope,
            is_public=False,
            asn="—",
            organization="—",
            network_cidr="—",
            error=None,
        )

    try:
        rdap = lookup_fn(address)
        asn, org, cidr = _rdap_to_row(address, rdap)
        return IpReportRow(
            address=address,
            ip_version=ver,
            scope=scope,
            is_public=True,
            asn=asn,
            organization=org,
            network_cidr=cidr,
            error=None,
        )
    except (BaseIpwhoisException, OSError, ValueError) as e:
        return IpReportRow(
            address=address,
            ip_version=ver,
            scope=scope,
            is_public=True,
            asn="—",
            organization="—",
            network_cidr="—",
            error=str(e) or type(e).__name__,
        )


def enrich_ips(
    addresses: list[str],
    *,
    lookup_fn=lookup_rdap,
) -> list[IpReportRow]:
    return [enrich_ip(a, lookup_fn=lookup_fn) for a in addresses]
