"""Volcado JSON de la respuesta RDAP (misma consulta que el informe HTML)."""

from __future__ import annotations

import argparse
import ipaddress
import json
import sys
from pathlib import Path

from ipwhois.exceptions import BaseIpwhoisException

from ipprovider.enrichment import _classify_scope, lookup_rdap


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ipprovider-rdap-json",
        description="Consulta RDAP para una IP pública y escribe el JSON (misma API que el informe).",
    )
    p.add_argument(
        "address",
        type=str,
        help="Dirección IPv4 o IPv6 pública",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        metavar="PATH",
        help="Escribir en archivo en lugar de la salida estándar",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        ip = ipaddress.ip_address(args.address.strip())
    except ValueError as e:
        print(f"Dirección IP no válida: {args.address!r} ({e})", file=sys.stderr)
        return 2

    scope, is_public = _classify_scope(ip)
    if not is_public:
        print(
            f"La IP no es pública (alcance: {scope}); RDAP solo aplica a direcciones globales.",
            file=sys.stderr,
        )
        return 2

    try:
        data = lookup_rdap(str(ip))
    except (BaseIpwhoisException, ValueError) as e:
        print(f"Error RDAP: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"Error de red: {e}", file=sys.stderr)
        return 1

    text = json.dumps(data, indent=2, ensure_ascii=False, default=str) + "\n"

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
