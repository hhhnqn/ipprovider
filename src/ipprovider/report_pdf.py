"""Generación del informe PDF con ReportLab."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ipprovider.enrichment import IpReportRow


def write_report_pdf(
    *,
    output_path: Path,
    source_pdf: Path,
    generated_at: datetime,
    rows: list[IpReportRow],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    story: list = []

    title = Paragraph(
        "<b>Informe de direcciones IP</b>",
        styles["Title"],
    )
    story.append(title)
    story.append(Spacer(1, 0.5 * cm))

    meta = Paragraph(
        f"Archivo origen: <i>{source_pdf}</i><br/>"
        f"Generado (UTC): {generated_at.strftime('%Y-%m-%d %H:%M:%S')}<br/>"
        f"Total de direcciones: {len(rows)}",
        styles["Normal"],
    )
    story.append(meta)
    story.append(Spacer(1, 0.6 * cm))

    if not rows:
        story.append(Paragraph("No se encontraron direcciones IP.", styles["Normal"]))
        doc.build(story)
        return

    table_data: list[list[str]] = [
        [
            "Dirección",
            "Versión",
            "Alcance",
            "ASN",
            "Organización / red",
            "CIDR",
            "Error RDAP",
        ],
    ]
    for r in rows:
        err = r.error or ""
        table_data.append(
            [
                r.address,
                r.ip_version,
                r.scope,
                r.asn,
                r.organization,
                r.network_cidr,
                err,
            ]
        )

    tbl = Table(table_data, repeatRows=1, hAlign="LEFT")
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
            ]
        )
    )
    story.append(tbl)
    doc.build(story)
