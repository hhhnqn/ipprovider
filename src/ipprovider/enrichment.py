"""Enriquecimiento de IPs públicas mediante RDAP (ipwhois)."""

from __future__ import annotations

import ipaddress
import sys
from dataclasses import dataclass
from typing import Any

from ipwhois import IPWhois
from ipwhois.exceptions import BaseIpwhoisException


@dataclass(frozen=True)
class RdapEntityContact:
    """Contacto RDAP por rol: titular, admin/técnico o abuso."""

    title: str
    handle: str
    name: str
    address: str
    phone: str
    email: str


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
    contacts: tuple[RdapEntityContact, ...] = ()
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
    """Concatena entradas de dirección de un contacto; preserva saltos de línea en cada valor."""
    if not addr:
        return ""
    parts: list[str] = []
    if isinstance(addr, list):
        for block in addr:
            if isinstance(block, dict):
                v = (block.get("value") or "").strip()
                if v:
                    parts.append(v)
            elif isinstance(block, str) and block.strip():
                parts.append(block.strip())
    elif isinstance(addr, str) and addr.strip():
        parts.append(addr.strip())
    return "\n".join(parts) if parts else ""


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


def _format_contact_emails(email: Any) -> str:
    if not email:
        return ""
    if isinstance(email, str) and email.strip():
        return email.strip()
    if isinstance(email, list):
        out: list[str] = []
        for e in email:
            if isinstance(e, dict):
                val = (e.get("value") or "").strip()
                if val:
                    out.append(val)
            elif isinstance(e, str) and e.strip():
                out.append(e.strip())
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


def _contact_from_object(o: dict[str, Any], title: str) -> RdapEntityContact:
    contact = o.get("contact") or {}
    if not isinstance(contact, dict):
        contact = {}
    handle = str(o.get("handle") or "").strip()
    name = (contact.get("name") or "").strip()
    addr = _format_contact_addresses(contact.get("address"))
    ph = _format_contact_phones(contact.get("phone"))
    em = _format_contact_emails(contact.get("email"))
    return RdapEntityContact(
        title=title,
        handle=handle,
        name=name,
        address=addr,
        phone=ph,
        email=em,
    )


def _extract_entity_contacts(rdap: dict[str, Any]) -> tuple[RdapEntityContact, ...]:
    """
    Titular (registrant), contacto admin/técnico, contacto de abuso.
    No repite el mismo handle en más de un bloque.
    """
    objects_list = _sorted_rdap_objects(rdap)
    seen_handles: set[str] = set()
    out: list[RdapEntityContact] = []

    def try_append(title: str, o: dict[str, Any]) -> None:
        h = str(o.get("handle") or "").strip()
        if h and h in seen_handles:
            return
        if h:
            seen_handles.add(h)
        block = _contact_from_object(o, title)
        if not any((block.name, block.address, block.phone, block.email)):
            return
        out.append(block)

    for o in objects_list:
        roles = set(o.get("roles") or [])
        if "registrant" in roles:
            try_append("Titular del recurso", o)
            break

    for o in objects_list:
        roles = set(o.get("roles") or [])
        if roles & {"administrative", "technical"}:
            try_append("Contacto administrativo / técnico", o)
            break

    for o in objects_list:
        roles = set(o.get("roles") or [])
        if "abuse" in roles:
            try_append("Contacto de abuso", o)
            break

    return tuple(out)


def _rdap_to_row(address: str, rdap: dict[str, Any]) -> tuple[str, str, str, tuple[RdapEntityContact, ...]]:
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

    contacts = _extract_entity_contacts(rdap)

    return (
        asn or "—",
        org or "—",
        cidr or "—",
        contacts,
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
            contacts=(),
            error=None,
        )

    try:
        rdap = lookup_fn(address)
        asn, org, cidr, contacts = _rdap_to_row(address, rdap)
        return IpReportRow(
            address=address,
            ip_version=ver,
            scope=scope,
            is_public=True,
            asn=asn,
            organization=org,
            network_cidr=cidr,
            contacts=contacts,
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
            contacts=(),
            error=str(e) or type(e).__name__,
        )


def enrich_ips(
    addresses: list[str],
    *,
    lookup_fn=lookup_rdap,
    progress: bool = False,
) -> list[IpReportRow]:
    """
    Si progress=True, escribe avance en stderr durante consultas RDAP (IPs públicas).
    Con muchas IPs públicas solo muestra una muestra periódica para no saturar la consola.
    """
    pub_total = sum(
        1
        for a in addresses
        if _classify_scope(ipaddress.ip_address(a))[1]
    )
    if progress and pub_total > 0:
        print(
            f"Consultando RDAP: {pub_total} dirección(es) pública(s)...",
            file=sys.stderr,
            flush=True,
        )

    out: list[IpReportRow] = []
    pub_done = 0
    # Con muchas IPs públicas, muestrear cada 10 consultas (y la 1.ª y la última).
    sample_every = 10 if pub_total > 50 else 1

    for a in addresses:
        ip = ipaddress.ip_address(a)
        _, is_pub = _classify_scope(ip)
        if is_pub and progress and pub_total > 0:
            pub_done += 1
            if (
                pub_total <= 50
                or pub_done in (1, pub_total)
                or pub_done % sample_every == 0
            ):
                print(
                    f"  RDAP {pub_done}/{pub_total}: {a} ...",
                    file=sys.stderr,
                    flush=True,
                )
        out.append(enrich_ip(a, lookup_fn=lookup_fn))
    return out
