"""Pruebas de extracción de texto desde PDF."""

from pathlib import Path

from reportlab.pdfgen import canvas

from ipprovider.ip_find import find_ips_in_text
from ipprovider.pdf_extract import extract_text_from_pdf


def _write_pdf_with_lines(path: Path, lines: list[str]) -> None:
    c = canvas.Canvas(str(path))
    y = 800
    for line in lines:
        c.drawString(72, y, line)
        y -= 16
    c.save()


def test_extract_and_find_ips(tmp_path):
    pdf = tmp_path / "sample.pdf"
    _write_pdf_with_lines(
        pdf,
        [
            "IPs: 198.51.100.1 y 2001:db8:abcd::1",
            "Otra línea 10.0.0.1",
        ],
    )
    text = extract_text_from_pdf(pdf)
    assert "198.51.100.1" in text
    ips = find_ips_in_text(text)
    assert "198.51.100.1" in ips
    assert "2001:db8:abcd::1" in ips
    assert "10.0.0.1" in ips
