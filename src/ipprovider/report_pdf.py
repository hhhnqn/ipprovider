"""Generación del informe PDF con ReportLab."""

from __future__ import annotations

import html
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ipprovider.enrichment import IpReportRow

# Pesos relativos por columna (suman 1.0); más ancho para texto largo.
_COL_WEIGHTS_RAW = (
    0.075,  # Dirección
    0.038,  # Versión
    0.055,  # Alcance
    0.048,  # ASN
    0.13,  # Organización / red
    0.075,  # CIDR
    0.11,  # Responsable
    0.195,  # Domicilio
    0.038,  # País
    0.095,  # Teléfono
)
_s = sum(_COL_WEIGHTS_RAW)
_COL_WEIGHTS = tuple(w / _s for w in _COL_WEIGHTS_RAW)


def _cell_text(s: str) -> str:
    t = html.escape(s or "", quote=False)
    return t.replace("\n", "<br/>")


def write_report_pdf(
    *,
    output_path: Path,
    source_pdf: Path,
    rows: list[IpReportRow],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    page_size = landscape(A4)
    left_m = 1.2 * cm
    right_m = 1.2 * cm
    top_m = 1.6 * cm
    bottom_m = 1.6 * cm

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=page_size,
        rightMargin=right_m,
        leftMargin=left_m,
        topMargin=top_m,
        bottomMargin=bottom_m,
    )

    usable_w = page_size[0] - left_m - right_m
    col_widths = [usable_w * w for w in _COL_WEIGHTS]
    drift = usable_w - sum(col_widths)
    if col_widths:
        col_widths[-1] += drift

    styles = getSampleStyleSheet()
    cell_style = ParagraphStyle(
        "tbl_cell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.2,
        leading=7.3,
        alignment=TA_LEFT,
        spaceBefore=0,
        spaceAfter=0,
        leftIndent=1,
        rightIndent=1,
    )
    header_style = ParagraphStyle(
        "tbl_head",
        parent=cell_style,
        fontName="Helvetica-Bold",
        textColor=colors.whitesmoke,
    )

    story: list = []

    story.append(
        Paragraph(
            "<b>Informe de direcciones IP</b>",
            styles["Title"],
        )
    )
    story.append(Spacer(1, 0.35 * cm))

    story.append(
        Paragraph(
            f"Archivo origen: <i>{html.escape(source_pdf.name, quote=False)}</i><br/>"
            f"Total de direcciones: {len(rows)}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.45 * cm))

    if not rows:
        story.append(Paragraph("No se encontraron direcciones IP.", styles["Normal"]))
        doc.build(story)
        return

    headers = [
        "Dirección",
        "Versión",
        "Alcance",
        "ASN",
        "Organización / red",
        "CIDR",
        "Responsable",
        "Domicilio",
        "País",
        "Teléfono",
    ]
    table_data: list[list[Paragraph]] = [
        [Paragraph(_cell_text(h), header_style) for h in headers],
    ]

    for r in rows:
        table_data.append(
            [
                Paragraph(_cell_text(r.address), cell_style),
                Paragraph(_cell_text(r.ip_version), cell_style),
                Paragraph(_cell_text(r.scope), cell_style),
                Paragraph(_cell_text(r.asn), cell_style),
                Paragraph(_cell_text(r.organization), cell_style),
                Paragraph(_cell_text(r.network_cidr), cell_style),
                Paragraph(_cell_text(r.responsible), cell_style),
                Paragraph(_cell_text(r.postal_address), cell_style),
                Paragraph(_cell_text(r.country), cell_style),
                Paragraph(_cell_text(r.phone), cell_style),
            ]
        )

    tbl = Table(
        table_data,
        colWidths=col_widths,
        repeatRows=1,
        hAlign="LEFT",
        splitByRow=1,
    )
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                ("GRID", (0, 0), (-1, -1), 0.2, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
            ]
        )
    )
    story.append(tbl)
    doc.build(story)
