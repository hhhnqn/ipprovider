"""Pruebas de enriquecimiento RDAP (mockeado)."""

import pytest

from ipprovider.enrichment import IpReportRow, enrich_ip, enrich_ips


def test_private_skips_lookup():
    r = enrich_ip("192.168.0.1", lookup_fn=lambda _: None)
    assert r.is_public is False
    assert r.scope == "privada"
    assert r.asn == "—"
    assert r.contacts == ()


def test_loopback_skips_lookup():
    r = enrich_ip("127.0.0.1", lookup_fn=lambda _: pytest.fail("no RDAP"))
    assert r.scope == "loopback"


def test_public_uses_lookup(sample_rdap_response):
    r = enrich_ip("8.8.8.8", lookup_fn=lambda _: sample_rdap_response)
    assert r.is_public is True
    assert r.scope == "pública"
    assert r.asn == "64496"
    assert "EXAMPLE" in r.organization
    assert len(r.contacts) == 1
    c0 = r.contacts[0]
    assert c0.title == "Titular del recurso"
    assert c0.name == "Example Maintainer"
    assert "Madrid" in c0.address
    assert "+34 900 000 000" in c0.phone


def test_rdap_three_entities_titular_admin_abuse(lacnic_style_rdap_response):
    r = enrich_ip("200.0.0.1", lookup_fn=lambda _: lacnic_style_rdap_response)
    assert r.organization == "EMPRESA-AS"
    assert len(r.contacts) == 3
    assert r.contacts[0].title == "Titular del recurso"
    assert r.contacts[0].name == "Empresa S.A."
    assert "Av. Corrientes" in r.contacts[0].address
    assert r.contacts[1].title == "Contacto administrativo / técnico"
    assert "169" in r.contacts[1].address
    assert r.contacts[1].name == "Luis Francisco Pérez Sánchez"
    assert "admin@example.test" in r.contacts[1].email
    assert r.contacts[2].title == "Contacto de abuso"
    assert r.contacts[2].name == "Abuse Desk"
    assert "abuse@example.test" in r.contacts[2].email


def test_lookup_error_surfaces():
    def boom(_):
        raise ValueError("fallo simulado")

    r = enrich_ip("8.8.8.8", lookup_fn=boom)
    assert r.error == "fallo simulado"
    assert r.contacts == ()


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
    assert len(rows[1].contacts) == 1
