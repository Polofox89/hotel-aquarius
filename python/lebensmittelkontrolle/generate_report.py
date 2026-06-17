"""Generator für Lebensmittelkontroll-Berichte als PDF.

Liest die Berichtsdaten aus einer JSON-Datei und erzeugt einen sauber
formatierten, mehrseitigen PDF-Bericht mit:

* Kopfzeile (Behörde/Dienststelle, optionales Logo)
* Betriebs- und Kontrolldaten
* Mängelliste als Karten mit Belegfoto und Bewertungs-Badge
* Gesamtbewertung und nächste Schritte
* Unterschriftenzeile

Aufruf::

    python generate_report.py report_data.json --out output/bericht.pdf
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# --- Farbpalette (zurückhaltend, amtlich) --------------------------------

PRIMARY = colors.HexColor("#1f3a5f")      # dunkles Blau (Kopf/Überschriften)
ACCENT = colors.HexColor("#2c6e8f")       # sekundäres Blau
LIGHT_BG = colors.HexColor("#eef2f6")     # heller Tabellenhintergrund
BORDER = colors.HexColor("#c8d2dc")       # Rahmenfarbe

# Bewertungsstufen -> Farbe (Badge-Hintergrund)
SEVERITY_COLORS: dict[str, colors.Color] = {
    "geringfügig": colors.HexColor("#3a8a3a"),
    "geringfuegig": colors.HexColor("#3a8a3a"),
    "erheblich": colors.HexColor("#d98b00"),
    "gravierend": colors.HexColor("#c0392b"),
}


def _severity_color(bewertung: str) -> colors.Color:
    """Liefert die Badge-Farbe für eine Bewertungsstufe."""
    return SEVERITY_COLORS.get(bewertung.strip().lower(), ACCENT)


def _styles() -> dict[str, ParagraphStyle]:
    """Erzeugt die im Bericht verwendeten Absatzstile."""
    base = getSampleStyleSheet()
    styles: dict[str, ParagraphStyle] = {}

    styles["title"] = ParagraphStyle(
        "title", parent=base["Title"], fontSize=18, textColor=PRIMARY,
        spaceAfter=2, alignment=TA_LEFT, leading=22,
    )
    styles["subtitle"] = ParagraphStyle(
        "subtitle", parent=base["Normal"], fontSize=10, textColor=ACCENT,
        spaceAfter=6,
    )
    styles["authority"] = ParagraphStyle(
        "authority", parent=base["Normal"], fontSize=9, textColor=colors.HexColor("#33414f"),
        leading=12,
    )
    styles["h2"] = ParagraphStyle(
        "h2", parent=base["Heading2"], fontSize=12, textColor=PRIMARY,
        spaceBefore=10, spaceAfter=6,
    )
    styles["label"] = ParagraphStyle(
        "label", parent=base["Normal"], fontSize=8, textColor=colors.HexColor("#6b7785"),
    )
    styles["value"] = ParagraphStyle(
        "value", parent=base["Normal"], fontSize=9.5, textColor=colors.black, leading=12,
    )
    styles["defect_title"] = ParagraphStyle(
        "defect_title", parent=base["Normal"], fontSize=11, textColor=PRIMARY,
        spaceAfter=2, leading=14,
    )
    styles["body"] = ParagraphStyle(
        "body", parent=base["Normal"], fontSize=9.5, leading=13,
    )
    styles["badge"] = ParagraphStyle(
        "badge", parent=base["Normal"], fontSize=8, textColor=colors.white,
        alignment=TA_CENTER, leading=10,
    )
    styles["small"] = ParagraphStyle(
        "small", parent=base["Normal"], fontSize=7.5,
        textColor=colors.HexColor("#6b7785"),
    )
    styles["footer"] = ParagraphStyle(
        "footer", parent=base["Normal"], fontSize=7.5,
        textColor=colors.HexColor("#8a96a3"), alignment=TA_CENTER,
    )
    return styles


def _info_table(rows: list[tuple[str, str]], styles, col_widths) -> Table:
    """Baut eine zweispaltige Label/Wert-Tabelle."""
    data = []
    for label, value in rows:
        data.append([
            Paragraph(label, styles["label"]),
            Paragraph(value or "—", styles["value"]),
        ])
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def _data_box(title: str, rows: list[tuple[str, str]], styles, width) -> Table:
    """Rahmt eine Info-Tabelle als Box mit Titelzeile ein."""
    inner = _info_table(rows, styles, [width * 0.34, width * 0.66 - 12])
    header = Paragraph(f"<b>{title}</b>", ParagraphStyle(
        "boxhdr", fontSize=10, textColor=colors.white,
    ))
    box = Table([[header], [inner]], colWidths=[width])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (0, 0), colors.white),
        ("TOPPADDING", (0, 0), (0, 0), 5),
        ("BOTTOMPADDING", (0, 0), (0, 0), 5),
        ("LEFTPADDING", (0, 0), (0, 0), 8),
        ("BACKGROUND", (0, 1), (0, 1), LIGHT_BG),
        ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
        ("TOPPADDING", (0, 1), (0, 1), 4),
        ("BOTTOMPADDING", (0, 1), (0, 1), 6),
    ]))
    return box


def _scaled_image(path: Path, max_w: float, max_h: float) -> Image | None:
    """Lädt ein Bild und skaliert es proportional in den erlaubten Rahmen."""
    if not path.exists():
        return None
    reader = ImageReader(str(path))
    iw, ih = reader.getSize()
    if iw == 0 or ih == 0:
        return None
    ratio = min(max_w / iw, max_h / ih)
    return Image(str(path), width=iw * ratio, height=ih * ratio)


def _defect_card(defect: dict[str, Any], styles, content_width: float) -> Table:
    """Erzeugt eine Mängel-Karte (Text links, Belegfoto rechts)."""
    nr = defect.get("nr", "")
    titel = defect.get("titel", "")
    bewertung = defect.get("bewertung", "")

    badge = Table(
        [[Paragraph(bewertung.upper(), styles["badge"])]],
        colWidths=[3.2 * cm],
    )
    badge.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _severity_color(bewertung)),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))

    # Textspalte zusammenbauen
    text_flow: list[Any] = [
        Paragraph(f"<b>Nr. {nr} – {titel}</b>", styles["defect_title"]),
        Spacer(1, 2),
        badge,
        Spacer(1, 5),
    ]
    detail_rows = [
        ("Bereich", defect.get("bereich", "")),
        ("Feststellung", defect.get("beschreibung", "")),
        ("Rechtsgrundlage", defect.get("rechtsgrundlage", "")),
        ("Maßnahme / Auflage", defect.get("massnahme", "")),
        ("Frist", defect.get("frist", "")),
    ]
    for label, value in detail_rows:
        if value:
            text_flow.append(
                Paragraph(f"<b>{label}:</b> {value}", styles["body"])
            )
            text_flow.append(Spacer(1, 2))
    if defect.get("video_quelle"):
        text_flow.append(Spacer(1, 2))
        text_flow.append(
            Paragraph(f"Quelle: {defect['video_quelle']}", styles["small"])
        )

    # Bildspalte
    photo_w = content_width * 0.34
    text_w = content_width * 0.66 - 10
    foto = defect.get("foto")
    image_cell: Any = ""
    if foto:
        img = _scaled_image(Path(foto), photo_w - 8, 6.5 * cm)
        if img is not None:
            caption = Paragraph(
                defect.get("foto_text", "Belegfoto (Standbild aus Video)"),
                styles["small"],
            )
            image_cell = [img, Spacer(1, 2), caption]
        else:
            image_cell = Paragraph("[Foto nicht gefunden]", styles["small"])

    card = Table(
        [[text_flow, image_cell]],
        colWidths=[text_w, photo_w],
    )
    card.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEAFTER", (0, 0), (0, 0), 0.4, BORDER),
    ]))
    return card


def _build_header(data: dict[str, Any], styles, content_width: float) -> list[Any]:
    """Baut den Kopfbereich des Berichts (Behörde + Titel)."""
    behoerde = data.get("behoerde", {})
    auth_lines = [
        f"<b>{behoerde.get('name', 'Behörde / Dienststelle')}</b>",
        behoerde.get("dienststelle", ""),
        behoerde.get("anschrift", ""),
        behoerde.get("kontakt", ""),
    ]
    auth_text = "<br/>".join(line for line in auth_lines if line)
    auth_para = Paragraph(auth_text, styles["authority"])

    logo_cell: Any = ""
    logo = behoerde.get("logo")
    if logo and Path(logo).exists():
        img = _scaled_image(Path(logo), 4.5 * cm, 2.2 * cm)
        if img is not None:
            logo_cell = img

    head = Table([[auth_para, logo_cell]], colWidths=[content_width * 0.65, content_width * 0.35])
    head.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))

    flow: list[Any] = [head, Spacer(1, 8)]
    rule = Table([[""]], colWidths=[content_width], rowHeights=[2])
    rule.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PRIMARY)]))
    flow.append(rule)
    flow.append(Spacer(1, 10))

    titel = data.get("titel", "Kontrollbericht – Lebensmittelüberwachung")
    flow.append(Paragraph(titel, styles["title"]))
    flow.append(Paragraph(
        data.get("untertitel", "Bericht über die amtliche Kontrolle gemäß VO (EU) 2017/625"),
        styles["subtitle"],
    ))
    flow.append(Spacer(1, 8))
    return flow


def build_report(data: dict[str, Any], output_path: Path) -> Path:
    """Erzeugt den PDF-Bericht aus den übergebenen Daten.

    Args:
        data: Berichtsdaten (siehe report_data.example.json).
        output_path: Zielpfad für das PDF.

    Returns:
        Pfad zur erzeugten PDF-Datei.
    """
    styles = _styles()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    margin = 1.8 * cm
    content_width = A4[0] - 2 * margin

    def _on_page(canvas_obj, doc) -> None:
        """Zeichnet die Fußzeile mit Seitenzahl auf jede Seite."""
        canvas_obj.saveState()
        footer = (
            f"{data.get('behoerde', {}).get('name', '')}  ·  "
            f"Betrieb: {data.get('betrieb', {}).get('name', '')}  ·  "
            f"Seite {doc.page}"
        )
        canvas_obj.setFont("Helvetica", 7.5)
        canvas_obj.setFillColor(colors.HexColor("#8a96a3"))
        canvas_obj.drawCentredString(A4[0] / 2, 1.1 * cm, footer)
        canvas_obj.setStrokeColor(BORDER)
        canvas_obj.setLineWidth(0.4)
        canvas_obj.line(margin, 1.5 * cm, A4[0] - margin, 1.5 * cm)
        canvas_obj.restoreState()

    doc = BaseDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=margin, rightMargin=margin,
        topMargin=margin, bottomMargin=2 * cm,
        title=data.get("titel", "Kontrollbericht"),
        author=data.get("kontrolleur", {}).get("name", ""),
    )
    frame = Frame(margin, 2 * cm, content_width, A4[1] - margin - 2 * cm, id="main")
    doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=_on_page)])

    flow: list[Any] = []
    flow += _build_header(data, styles, content_width)

    # Betriebs- und Kontrolldaten nebeneinander
    betrieb = data.get("betrieb", {})
    kontrolle = data.get("kontrolle", {})
    kontrolleur = data.get("kontrolleur", {})

    betrieb_rows = [
        ("Betrieb", betrieb.get("name", "")),
        ("Inhaber/Verantw.", betrieb.get("inhaber", "")),
        ("Anschrift", betrieb.get("anschrift", "")),
        ("Betriebsart", betrieb.get("betriebsart", "")),
        ("Registriernr.", betrieb.get("registriernummer", "")),
    ]
    kontrolle_rows = [
        ("Datum", kontrolle.get("datum", "")),
        ("Uhrzeit", kontrolle.get("uhrzeit", "")),
        ("Anlass", kontrolle.get("anlass", "")),
        ("Kontrolleur/in", kontrolleur.get("name", "")),
        ("Anwesend", kontrolle.get("anwesend", "")),
    ]

    half = (content_width - 8) / 2
    box_l = _data_box("Betriebsdaten", betrieb_rows, styles, half)
    box_r = _data_box("Kontrolldaten", kontrolle_rows, styles, half)
    boxes = Table([[box_l, box_r]], colWidths=[half, half], hAlign="LEFT")
    boxes.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 8),
        ("RIGHTPADDING", (1, 0), (1, 0), 0),
    ]))
    flow.append(boxes)
    flow.append(Spacer(1, 14))

    # Mängelliste
    maengel = data.get("maengel", [])
    flow.append(Paragraph(
        f"Mängelliste ({len(maengel)} Feststellung{'en' if len(maengel) != 1 else ''})",
        styles["h2"],
    ))
    flow.append(Spacer(1, 4))
    if not maengel:
        flow.append(Paragraph(
            "Bei der Kontrolle wurden keine Mängel festgestellt.", styles["body"]
        ))
    for defect in maengel:
        flow.append(_defect_card(defect, styles, content_width))
        flow.append(Spacer(1, 8))

    # Gesamtbewertung
    if data.get("gesamtbewertung") or data.get("naechste_schritte"):
        flow.append(Spacer(1, 6))
        flow.append(Paragraph("Gesamtbewertung &amp; weiteres Vorgehen", styles["h2"]))
        if data.get("gesamtbewertung"):
            flow.append(Paragraph(data["gesamtbewertung"], styles["body"]))
            flow.append(Spacer(1, 4))
        if data.get("naechste_schritte"):
            flow.append(Paragraph(f"<b>Nächste Schritte:</b> {data['naechste_schritte']}", styles["body"]))

    # Unterschriftenzeile
    flow.append(Spacer(1, 26))
    sig = Table(
        [
            ["", ""],
            [
                Paragraph("Ort, Datum", styles["small"]),
                Paragraph("Unterschrift Kontrolleur/in", styles["small"]),
            ],
        ],
        colWidths=[half, half],
        rowHeights=[0.9 * cm, 0.5 * cm],
    )
    sig.setStyle(TableStyle([
        ("LINEABOVE", (0, 1), (0, 1), 0.6, colors.black),
        ("LINEABOVE", (1, 1), (1, 1), 0.6, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    flow.append(sig)

    erstellt = datetime.now().strftime("%d.%m.%Y %H:%M")
    flow.append(Spacer(1, 8))
    flow.append(Paragraph(
        f"Automatisch erstellter Entwurf – {erstellt} Uhr. "
        f"Standbilder wurden aus den vom Kontrolleur bereitgestellten Videos extrahiert.",
        styles["small"],
    ))

    doc.build(flow)
    return output_path


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Lebensmittelkontroll-Bericht als PDF erstellen.")
    parser.add_argument("data", type=Path, help="JSON-Datei mit den Berichtsdaten")
    parser.add_argument(
        "--out", type=Path, default=Path("output/kontrollbericht.pdf"),
        help="Zielpfad für das PDF",
    )
    args = parser.parse_args()

    with args.data.open(encoding="utf-8") as fh:
        data = json.load(fh)

    path = build_report(data, args.out)
    print(f"Bericht erstellt: {path}")


if __name__ == "__main__":
    main()
