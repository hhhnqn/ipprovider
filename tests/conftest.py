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
