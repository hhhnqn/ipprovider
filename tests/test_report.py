"""Pruebas de generación del informe HTML."""

from pathlib import Path

from ipprovider.enrichment import IpReportRow, RdapEntityContact
from ipprovider.report_html import write_report_html


def _sample_contacts() -> tuple[RdapEntityContact, ...]:
    return (
        RdapEntityContact(
            title="Titular del recurso",
            handle="ORG-EX",
            name="Example Maintainer",
            address="Calle Demo 1\nCiudad",
            phone="+34 900 111 222",
            email="",
        ),
    )


def test_report_creates_html_with_rows(tmp_path):
    out = tmp_path / "out.html"
    src = tmp_path / "in.pdf"

    rows = [
        IpReportRow(
            address="192.168.1.1",
            ip_version="IPv4",
            scope="privada",
            is_public=False,
            asn="—",
            organization="—",
            network_cidr="—",
            contacts=(),
        ),
        IpReportRow(
            address="192.0.2.1",
            ip_version="IPv4",
            scope="pública",
            is_public=True,
            asn="64496",
            organization="Example Org",
            network_cidr="192.0.2.0/24",
            contacts=_sample_contacts(),
        ),
    ]

    write_report_html(
        output_path=out,
        source_file=src,
        rows=rows,
    )

    assert out.is_file()
    html_text = out.read_text(encoding="utf-8")
    assert "192.168.1.1" in html_text
    assert "Example Org" in html_text
    assert "Example Maintainer" in html_text
    assert "Calle Demo 1" in html_text
    assert "Contactos" in html_text
    assert "in.pdf" in html_text
    assert "<table>" in html_text
    assert "rdap-entity" in html_text


def test_report_contacts_multiline_br(tmp_path):
    out = tmp_path / "multi.html"
    rows = [
        IpReportRow(
            address="200.0.0.1",
            ip_version="IPv4",
            scope="pública",
            is_public=True,
            asn="12345",
            organization="Empresa",
            network_cidr="200.0.0.0/24",
            contacts=(
                RdapEntityContact(
                    title="Contacto administrativo / técnico",
                    handle="MBC",
                    name="Persona",
                    address="Línea 1\nLínea 169",
                    phone="—",
                    email="",
                ),
            ),
        ),
    ]
    write_report_html(output_path=out, source_file=tmp_path / "src.txt", rows=rows)
    html_text = out.read_text(encoding="utf-8")
    assert "<br />" in html_text
    assert "Línea 169" in html_text


def test_report_empty(tmp_path):
    out = tmp_path / "empty.html"
    write_report_html(
        output_path=out,
        source_file=Path("n/a.xlsx"),
        rows=[],
    )
    html_text = out.read_text(encoding="utf-8")
    assert "No se encontraron" in html_text
    assert "<table>" not in html_text
