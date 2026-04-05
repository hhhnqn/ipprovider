"""Configuración compartida de pytest."""

import pytest


@pytest.fixture
def sample_rdap_response():
    return {
        "asn": 64496,
        "asn_description": "EXAMPLE-AS",
        "network": {
            "name": "EXAMPLE-NET",
            "cidr": "192.0.2.0/24",
            "country": "ES",
        },
        "objects": {
            "ORG-EXAMPLE": {
                "handle": "ORG-EXAMPLE",
                "roles": ["registrant"],
                "contact": {
                    "name": "Example Maintainer",
                    "kind": "org",
                    "address": [
                        {
                            "type": None,
                            "value": "Calle Falsa 123\n28001 Madrid\nEspaña",
                        }
                    ],
                    "phone": [{"type": "voice", "value": "+34 900 000 000"}],
                },
            },
        },
    }


@pytest.fixture
def lacnic_style_rdap_response():
    """Registrant (empresa) + administrative (persona y segunda línea de dirección con «169»)."""
    return {
        "asn": 12345,
        "asn_description": "EMPRESA-AS",
        "network": {
            "name": "EMPRESA-NET",
            "cidr": "200.0.0.0/24",
            "country": "AR",
        },
        "objects": {
            "ORG-1": {
                "handle": "ORG-1",
                "roles": ["registrant"],
                "contact": {
                    "name": "Empresa S.A.",
                    "kind": "org",
                    "address": [
                        {
                            "type": None,
                            "value": "Av. Corrientes 1000\nC1000 CABA",
                        }
                    ],
                    "phone": [{"type": "voice", "value": "+54 11 0000-0000"}],
                },
            },
            "PER-1": {
                "handle": "PER-1",
                "roles": ["administrative"],
                "contact": {
                    "name": "Luis Francisco Pérez Sánchez",
                    "kind": "individual",
                    "address": [
                        {
                            "type": None,
                            "value": "Av. Independencia, 169, PB\n1099 - Buenos Aires - CF",
                        }
                    ],
                    "phone": [{"type": "voice", "value": "+54 11 1111-1111"}],
                    "email": [{"type": None, "value": "admin@example.test"}],
                },
            },
            "TEA-1": {
                "handle": "TEA-1",
                "roles": ["abuse"],
                "contact": {
                    "name": "Abuse Desk",
                    "kind": "individual",
                    "address": [{"type": None, "value": "Av. Abuse 1\nCABA"}],
                    "phone": [{"type": "voice", "value": "+54 11 9999-9999"}],
                    "email": [{"type": None, "value": "abuse@example.test"}],
                },
            },
        },
    }
