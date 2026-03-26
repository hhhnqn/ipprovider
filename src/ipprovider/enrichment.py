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
    responsible: str = "—"
    postal_address: str = "—"
    country: str = "—"
    phone: str = "—"
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


def _roles_priority(roles: Any) -> int:
    if not roles or not isinstance(roles, list):
        return 50
    rset = set(roles)
    if "registrant" in rset:
        return 0
    if "administrative" in rset:
        return 1
    if "technical" in rset:
        return 2
    if "abuse" in rset:
        return 3
    return 10


def _format_contact_addresses(addr: Any) -> str:
    if not addr:
        return ""
    parts: list[str] = []
    if isinstance(addr, list):
        for block in addr:
            if isinstance(block, dict):
                v = (block.get("value") or "").strip()
                if v:
                    parts.append(v.replace("\n", ", "))
            elif isinstance(block, str) and block.strip():
                parts.append(block.strip())
    elif isinstance(addr, str) and addr.strip():
        parts.append(addr.strip())
    return " | ".join(parts) if parts else ""


def _format_contact_phones(phone: Any) -> str:
    if not phone:
        return ""
    if isinstance(phone, str) and phone.strip():
        return phone.strip()
    if isinstance(phone, list):
        out: list[str] = []
        for p in phone:
            if isinstance(p, dict):
                val = (p.get("value") or "").strip()
                if val:
                    ptype = (p.get("type") or "").strip()
                    out.append(f"{val} ({ptype})" if ptype else val)
            elif isinstance(p, str) and p.strip():
                out.append(p.strip())
        return "; ".join(out)
    return ""


def _sorted_rdap_objects(rdap: dict[str, Any]) -> list[dict[str, Any]]:
    objs = rdap.get("objects") or {}
    if not isinstance(objs, dict):
        return []
    result: list[dict[str, Any]] = []
    for o in objs.values():
        if isinstance(o, dict):
            result.append(o)
    result.sort(key=lambda o: (_roles_priority(o.get("roles")), str(o.get("handle") or "")))
    return result


def _pick_contact_details(rdap: dict[str, Any]) -> tuple[str, str, str, str]:
    """responsible, postal_address, country, phone desde objects.contact y network."""
    network_obj = rdap.get("network") or {}
    country = ""
    if isinstance(network_obj, dict):
        c = network_obj.get("country")
        if c is not None and str(c).strip():
            country = str(c).strip()

    objects_list = _sorted_rdap_objects(rdap)
    responsible = ""
    postal_address = ""
    phone = ""

    for o in objects_list:
        contact = o.get("contact") or {}
        if not isinstance(contact, dict):
            continue
        name = (contact.get("name") or "").strip()
        addr = _format_contact_addresses(contact.get("address"))
        ph = _format_contact_phones(contact.get("phone"))
        if not responsible and name:
            responsible = name
        if not postal_address and addr:
            postal_address = addr
        if not phone and ph:
            phone = ph
        if responsible and postal_address and phone:
            break

    if not responsible or not postal_address:
        for o in objects_list:
            contact = o.get("contact") or {}
            if not isinstance(contact, dict):
                continue
            name = (contact.get("name") or "").strip()
            addr = _format_contact_addresses(contact.get("address"))
            if not responsible and name:
                responsible = name
            if not postal_address and addr:
                postal_address = addr
            if responsible and postal_address:
                break

    if not phone:
        for o in objects_list:
            contact = o.get("contact") or {}
            if not isinstance(contact, dict):
                continue
            ph = _format_contact_phones(contact.get("phone"))
            if ph:
                phone = ph
                break

    if not country and postal_address:
        tail = postal_address.split(",")[-1].strip()
        if len(tail) <= 64 and tail.replace(" ", "").isalpha():
            country = tail

    return responsible, postal_address, country, phone


def _rdap_to_row(address: str, rdap: dict[str, Any]) -> tuple[str, str, str, str, str, str, str]:
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

    responsible, postal_address, country, phone = _pick_contact_details(rdap)

    def dash(s: str) -> str:
        return s if s else "—"

    return (
        asn or "—",
        org or "—",
        cidr or "—",
        dash(responsible),
        dash(postal_address),
        dash(country),
        dash(phone),
    )


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
            responsible="—",
            postal_address="—",
            country="—",
            phone="—",
            error=None,
        )

    try:
        rdap = lookup_fn(address)
        asn, org, cidr, responsible, postal_address, country, phone = _rdap_to_row(address, rdap)
        return IpReportRow(
            address=address,
            ip_version=ver,
            scope=scope,
            is_public=True,
            asn=asn,
            organization=org,
            network_cidr=cidr,
            responsible=responsible,
            postal_address=postal_address,
            country=country,
            phone=phone,
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
            responsible="—",
            postal_address="—",
            country="—",
            phone="—",
            error=str(e) or type(e).__name__,
        )


def enrich_ips(
    addresses: list[str],
    *,
    lookup_fn=lookup_rdap,
) -> list[IpReportRow]:
    return [enrich_ip(a, lookup_fn=lookup_fn) for a in addresses]
