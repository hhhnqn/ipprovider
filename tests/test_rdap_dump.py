"""Pruebas del volcado JSON RDAP (sin red)."""

from unittest.mock import patch

from ipprovider.rdap_dump import main


def test_rdap_dump_json_stdout(capsys):
    sample = {"asn": 64496, "network": {"cidr": "192.0.2.0/24", "country": "ES"}}
    with patch("ipprovider.rdap_dump.lookup_rdap", return_value=sample):
        assert main(["8.8.8.8"]) == 0
    out = capsys.readouterr().out
    assert '"asn": 64496' in out
    assert "network" in out


def test_rdap_dump_rejects_private():
    assert main(["192.168.0.1"]) == 2


def test_rdap_dump_invalid_ip():
    assert main(["not-an-ip"]) == 2


def test_rdap_dump_writes_output_file(tmp_path):
    sample = {"asn": 1}
    out = tmp_path / "rdap.json"
    with patch("ipprovider.rdap_dump.lookup_rdap", return_value=sample):
        assert main(["8.8.8.8", "-o", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert '"asn": 1' in text
