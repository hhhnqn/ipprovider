"""Interfaz de línea de comandos."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ipprovider.document_extract import SUPPORTED_EXTENSIONS, extract_text
from ipprovider.enrichment import IpReportRow, enrich_ips
from ipprovider.ip_find import find_ips_in_text
from ipprovider.report_html import write_report_html


def _print_runtime_summary(addresses: list[str], rows: list[IpReportRow], *, quiet: bool) -> None:
    if quiet:
        return
    n = len(addresses)
    print(f"\nDirecciones IP encontradas: {n}", flush=True)
    for i, addr in enumerate(addresses, 1):
        print(f"  {i}. {addr}", flush=True)
    print("\nProcesamiento (RDAP en IPs públicas):", flush=True)
    for r in rows:
        line = f"  {r.address}  {r.ip_version}  {r.scope}"
        if r.is_public:
            org = (r.organization or "—").replace("\n", " ")
            if len(org) > 60:
                org = org[:57] + "..."
            extra = f"  ASN {r.asn}  {org}  CIDR {r.network_cidr}"
            if r.error:
                extra += f"  [RDAP: {r.error}]"
            line += "\n    " + extra
        print(line, flush=True)


def build_parser() -> argparse.ArgumentParser:
    exts = ", ".join(sorted(SUPPORTED_EXTENSIONS))
    p = argparse.ArgumentParser(
        prog="ipprovider",
        description=(
            "Extrae direcciones IPv4 e IPv6 de un documento (PDF, Excel o Word) "
            "y genera un informe HTML con datos RDAP para IPs públicas."
        ),
    )
    p.add_argument(
        "document",
        type=Path,
        help=f"Archivo de entrada ({exts})",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Ruta del informe HTML de salida (por defecto: informe_ips.html en el directorio actual)",
    )
    p.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="No mostrar avance (lectura Excel, RDAP, listado de IPs ni resumen)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    doc_path: Path = args.document
    if not doc_path.is_file():
        print(f"Error: no existe el archivo: {doc_path}", file=sys.stderr)
        return 1

    try:
        text = extract_text(doc_path, progress=not args.quiet)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error al leer el documento: {e}", file=sys.stderr)
        return 1

    if not text.strip():
        print(
            "Advertencia: no se extrajo texto del documento (¿PDF escaneado u hoja vacía?).",
            file=sys.stderr,
        )

    addresses = find_ips_in_text(text)
    rows = enrich_ips(addresses, progress=not args.quiet)
    _print_runtime_summary(addresses, rows, quiet=args.quiet)

    out = args.output
    if out is None:
        out = Path.cwd() / "informe_ips.html"

    try:
        write_report_html(
            output_path=out,
            source_file=doc_path,
            rows=rows,
        )
    except Exception as e:
        print(f"Error al escribir el informe: {e}", file=sys.stderr)
        return 1

    print(f"Informe generado: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
