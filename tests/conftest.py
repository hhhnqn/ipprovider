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
        },
    }
