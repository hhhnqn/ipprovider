"""Pruebas de enriquecimiento RDAP (mockeado)."""

import pytest

from ipprovider.enrichment import IpReportRow, enrich_ip, enrich_ips


def test_private_skips_lookup():
    r = enrich_ip("192.168.0.1", lookup_fn=lambda _: None)
    assert r.is_public is False
    assert r.scope == "privada"
    assert r.asn == "—"
    assert r.responsible == "—"


def test_loopback_skips_lookup():
    r = enrich_ip("127.0.0.1", lookup_fn=lambda _: pytest.fail("no RDAP"))
    assert r.scope == "loopback"


def test_public_uses_lookup(sample_rdap_response):
    # 192.0.2.0/24 es DOCUMENTATION (no global); 8.8.8.8 es pública real
    r = enrich_ip("8.8.8.8", lookup_fn=lambda _: sample_rdap_response)
    assert r.is_public is True
    assert r.scope == "pública"
    assert r.asn == "64496"
    assert "EXAMPLE" in r.organization
    assert r.responsible == "Example Maintainer"
    assert "Madrid" in r.postal_address
    assert r.country == "ES"
    assert "+34 900 000 000" in r.phone


def test_lookup_error_surfaces():
    def boom(_):
        raise ValueError("fallo simulado")

    r = enrich_ip("8.8.8.8", lookup_fn=boom)
    assert r.error == "fallo simulado"
    assert r.phone == "—"


def test_enrich_ips_list():
    rows = enrich_ips(
        ["192.168.1.1", "8.8.8.8"],
        lookup_fn=lambda _: {
            "asn": 1,
            "asn_description": "X",
            "network": {"cidr": "0.0.0.0/0", "country": "ZZ"},
            "objects": {
                "O1": {
                    "handle": "O1",
                    "roles": ["registrant"],
                    "contact": {
                        "name": "Org X",
                        "address": [{"value": "Somewhere"}],
                        "phone": [{"type": "voice", "value": "+1"}],
                    },
                }
            },
        },
    )
    assert len(rows) == 2
    assert rows[0].is_public is False
    assert rows[1].is_public is True
    assert rows[1].country == "ZZ"
