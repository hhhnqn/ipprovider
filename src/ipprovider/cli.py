"""Interfaz de línea de comandos."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from ipprovider.enrichment import enrich_ips
from ipprovider.ip_find import find_ips_in_text
from ipprovider.pdf_extract import extract_text_from_pdf
from ipprovider.report_pdf import write_report_pdf


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ipprovider",
        description="Extrae direcciones IPv4 e IPv6 de un PDF y genera un informe PDF con datos RDAP para IPs públicas.",
    )
    p.add_argument(
        "pdf",
        type=Path,
        help="Ruta al archivo PDF de entrada",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Ruta del informe PDF de salida (por defecto: informe_ips.pdf en el directorio actual)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    pdf_path: Path = args.pdf
    if not pdf_path.is_file():
        print(f"Error: no existe el archivo: {pdf_path}", file=sys.stderr)
        return 1

    try:
        text = extract_text_from_pdf(pdf_path)
    except Exception as e:
        print(f"Error al leer el PDF: {e}", file=sys.stderr)
        return 1

    if not text.strip():
        print(
            "Advertencia: el PDF no contiene texto extraíble (¿documento escaneado?).",
            file=sys.stderr,
        )

    rows = enrich_ips(find_ips_in_text(text))
    out = args.output
    if out is None:
        out = Path.cwd() / "informe_ips.pdf"

    generated_at = datetime.now(timezone.utc)
    try:
        write_report_pdf(
            output_path=out,
            source_pdf=pdf_path,
            generated_at=generated_at,
            rows=rows,
        )
    except Exception as e:
        print(f"Error al escribir el informe: {e}", file=sys.stderr)
        return 1

    print(f"Informe generado: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
