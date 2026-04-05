"""Generación del informe HTML."""

from __future__ import annotations

import html
from pathlib import Path

from ipprovider.enrichment import IpReportRow, RdapEntityContact


def _th(label: str) -> str:
    return f"    <th>{html.escape(label, quote=False)}</th>\n"


def _td(value: str) -> str:
    return f"    <td>{html.escape(value or '', quote=False)}</td>\n"


def _esc_multiline(s: str) -> str:
    esc = html.escape(s or "", quote=False)
    return esc.replace("\n", "<br />")


def _entity_block_html(c: RdapEntityContact) -> str:
    title_line = html.escape(c.title, quote=False)
    if c.handle:
        title_line += f' <span class="rdap-handle">({html.escape(c.handle, quote=False)})</span>'
    parts: list[str] = [f'<div class="rdap-entity-title">{title_line}</div>']
    if c.name:
        parts.append(
            f'<div class="rdap-field"><span class="rdap-k">Nombre:</span> '
            f'<span class="rdap-v">{_esc_multiline(c.name)}</span></div>'
        )
    if c.address:
        parts.append(
            f'<div class="rdap-field"><span class="rdap-k">Dirección:</span> '
            f'<span class="rdap-v">{_esc_multiline(c.address)}</span></div>'
        )
    if c.phone:
        parts.append(
            f'<div class="rdap-field"><span class="rdap-k">Teléfono:</span> '
            f'<span class="rdap-v">{_esc_multiline(c.phone)}</span></div>'
        )
    if c.email:
        parts.append(
            f'<div class="rdap-field"><span class="rdap-k">Email:</span> '
            f'<span class="rdap-v">{_esc_multiline(c.email)}</span></div>'
        )
    return f'<div class="rdap-entity">{"".join(parts)}</div>'


def _td_contacts(contacts: tuple[RdapEntityContact, ...]) -> str:
    if not contacts:
        return _td("—")
    inner = "".join(_entity_block_html(c) for c in contacts)
    return f'    <td class="rdap-contacts">{inner}</td>\n'


def write_report_html(
    *,
    output_path: Path,
    source_file: Path,
    rows: list[IpReportRow],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    headers = [
        "Dirección",
        "Versión",
        "Alcance",
        "ASN",
        "Organización / red",
        "CIDR",
        "Contactos",
    ]

    head_row = "".join(_th(h) for h in headers)

    body_rows: list[str] = []
    for r in rows:
        row_html = (
            "  <tr>\n"
            + "".join(
                [
                    _td(r.address),
                    _td(r.ip_version),
                    _td(r.scope),
                    _td(r.asn),
                    _td(r.organization),
                    _td(r.network_cidr),
                    _td_contacts(r.contacts),
                ]
            )
            + "  </tr>\n"
        )
        body_rows.append(row_html)

    if rows:
        table_block = (
            '<table>\n'
            "  <thead>\n"
            "  <tr>\n"
            f"{head_row}"
            "  </tr>\n"
            "  </thead>\n"
            "  <tbody>\n"
            f"{''.join(body_rows)}"
            "  </tbody>\n"
            "</table>\n"
        )
    else:
        table_block = '<p class="empty">No se encontraron direcciones IP.</p>\n'

    title = "Informe de direcciones IP"
    src_name = html.escape(source_file.name, quote=False)
    doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title, quote=False)}</title>
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
           margin: 1.5rem; line-height: 1.4; color: #1a1a1a; }}
    h1 {{ font-size: 1.35rem; margin-bottom: 0.75rem; }}
    .meta {{ margin-bottom: 1rem; color: #444; font-size: 0.95rem; }}
    table {{ border-collapse: collapse; width: 100%; table-layout: fixed; font-size: 0.82rem; }}
    th, td {{ border: 1px solid #ccc; padding: 0.35rem 0.5rem; vertical-align: top;
              word-wrap: break-word; overflow-wrap: anywhere; }}
    thead th {{ background: #4472c4; color: #f5f5f5; font-weight: 600; }}
    tbody tr:nth-child(even) {{ background: #f2f2f2; }}
    .empty {{ padding: 1rem 0; }}
    td.rdap-contacts {{ font-size: 0.78rem; }}
    .rdap-entity {{ margin-bottom: 0.85rem; padding-left: 0.45rem; border-left: 3px solid #4472c4; }}
    .rdap-entity:last-child {{ margin-bottom: 0; }}
    .rdap-entity-title {{ font-weight: 600; margin-bottom: 0.35rem; }}
    .rdap-handle {{ font-weight: 400; color: #444; }}
    .rdap-field {{ margin: 0.2rem 0; }}
    .rdap-k {{ color: #555; }}
  </style>
</head>
<body>
  <h1>{html.escape(title, quote=False)}</h1>
  <div class="meta">
    Archivo origen: <em>{src_name}</em><br />
    Total de direcciones: {len(rows)}
  </div>
{table_block}</body>
</html>
"""
    output_path.write_text(doc, encoding="utf-8")
