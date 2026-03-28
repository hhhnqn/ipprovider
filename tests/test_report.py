"""Pruebas de generación del informe PDF."""

from pathlib import Path

from pypdf import PdfReader

from ipprovider.enrichment import IpReportRow
from ipprovider.report_pdf import write_report_pdf


def test_report_creates_pdf_with_rows(tmp_path):
    out = tmp_path / "out.pdf"
    src = tmp_path / "in.pdf"
    src.write_bytes(b"%PDF-1.4\n")

    rows = [
        IpReportRow(
            address="192.168.1.1",
            ip_version="IPv4",
            scope="privada",
            is_public=False,
            asn="—",
            organization="—",
            network_cidr="—",
            responsible="—",
            postal_address="—",
            country="—",
            phone="—",
        ),
        IpReportRow(
            address="192.0.2.1",
            ip_version="IPv4",
            scope="pública",
            is_public=True,
            asn="64496",
            organization="Example Org",
            network_cidr="192.0.2.0/24",
            responsible="Example Maintainer",
            postal_address="Calle Demo 1, Ciudad",
            country="ES",
            phone="+34 900 111 222",
        ),
    ]

    write_report_pdf(
        output_path=out,
        source_pdf=src,
        rows=rows,
    )

    assert out.is_file()
    reader = PdfReader(str(out))
    assert len(reader.pages) >= 1
    text = "".join(page.extract_text() or "" for page in reader.pages)
    assert "192.168.1.1" in text
    assert "Example Org" in text
    assert "Example Maintainer" in text
    assert "Calle Demo 1" in text
    assert "Teléfono" in text


def test_report_empty(tmp_path):
    out = tmp_path / "empty.pdf"
    write_report_pdf(
        output_path=out,
        source_pdf=Path("n/a.pdf"),
        rows=[],
    )
    reader = PdfReader(str(out))
    assert len(reader.pages) >= 1
    text = reader.pages[0].extract_text() or ""
    assert "No se encontraron" in text
