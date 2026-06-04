"""HTML-Generator für Lebensmittelkontroll-Berichte.

Liest dieselbe ``report_data.json`` wie ``generate_report.py`` und erzeugt eine
eigenständige, portable HTML-Datei: Bilder werden als Base64-Data-URIs
eingebettet, sodass die Datei ohne externe Abhängigkeiten weitergegeben werden
kann. Das Layout entspricht dem PDF (Kopf, Daten-Boxen, Mängelkarten mit
Bewertungs-Badge, Unterschriftenzeile) und ist druckoptimiert (Browser:
„Drucken → Als PDF speichern").

Aufruf::

    python generate_report_html.py report_data.json --out output/bericht.html
"""

from __future__ import annotations

import base64
import html
import json
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Any

# Bewertungsstufe -> CSS-Klasse für das Badge
SEVERITY_CLASS = {
    "geringfügig": "badge-green",
    "geringfuegig": "badge-green",
    "erheblich": "badge-orange",
    "gravierend": "badge-red",
}

CSS = """
:root {
  --primary: #1f3a5f;
  --accent: #2c6e8f;
  --light: #eef2f6;
  --border: #c8d2dc;
  --muted: #6b7785;
}
* { box-sizing: border-box; }
body {
  font-family: "Helvetica Neue", Arial, sans-serif;
  color: #1c2733; margin: 0; background: #f4f6f8;
  font-size: 14px; line-height: 1.45;
}
.page {
  max-width: 820px; margin: 24px auto; background: #fff;
  padding: 40px 46px; box-shadow: 0 1px 8px rgba(0,0,0,.12);
}
.head { display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; }
.authority { font-size: 12.5px; color: #33414f; line-height: 1.5; }
.authority strong { color: var(--primary); }
.head img { max-height: 64px; max-width: 180px; }
.rule { height: 3px; background: var(--primary); margin: 14px 0 18px; }
h1 { font-size: 26px; color: var(--primary); margin: 0 0 2px; }
.subtitle { color: var(--accent); font-size: 13px; margin: 0 0 22px; }
.boxes { display: flex; gap: 16px; margin-bottom: 26px; }
.box { flex: 1; border: 1px solid var(--border); border-radius: 4px; overflow: hidden; }
.box .box-title { background: var(--primary); color: #fff; font-weight: 700; padding: 7px 12px; font-size: 13.5px; }
.box table { width: 100%; border-collapse: collapse; background: var(--light); }
.box td { padding: 4px 12px; vertical-align: top; font-size: 13px; }
.box td.label { color: var(--muted); width: 38%; font-size: 11.5px; }
h2 { font-size: 17px; color: var(--primary); margin: 26px 0 12px; }
.card {
  display: flex; gap: 14px; border: 1px solid var(--border); border-radius: 4px;
  padding: 14px 16px; margin-bottom: 14px; background: #fff;
  page-break-inside: avoid;
}
.card .text { flex: 2; min-width: 0; }
.card .photo { flex: 1; max-width: 240px; }
.card .photo img { width: 100%; border: 1px solid var(--border); border-radius: 3px; }
.card .caption { color: var(--muted); font-size: 11px; margin-top: 4px; }
.card h3 { font-size: 15px; color: var(--primary); margin: 0 0 8px; }
.card p { margin: 4px 0; font-size: 13px; }
.card .src { color: var(--muted); font-size: 11px; margin-top: 8px; }
.badge {
  display: inline-block; color: #fff; font-size: 11px; font-weight: 700;
  letter-spacing: .04em; padding: 3px 12px; border-radius: 3px; margin-bottom: 8px;
}
.badge-green { background: #3a8a3a; }
.badge-orange { background: #d98b00; }
.badge-red { background: #c0392b; }
.badge-default { background: var(--accent); }
.summary { margin-top: 20px; }
.signatures { display: flex; gap: 40px; margin-top: 54px; }
.sig { flex: 1; border-top: 1px solid #000; padding-top: 4px; font-size: 11.5px; color: var(--muted); }
.footer { margin-top: 28px; border-top: 1px solid var(--border); padding-top: 8px;
  text-align: center; color: var(--muted); font-size: 11px; }
.disclaimer { color: var(--muted); font-size: 11px; margin-top: 14px; }
@media print {
  body { background: #fff; }
  .page { box-shadow: none; margin: 0; max-width: none; padding: 0; }
  @page { margin: 16mm; }
}
"""


def _img_data_uri(path_str: str) -> str | None:
    """Lädt ein Bild und gibt es als Base64-Data-URI zurück (oder None)."""
    if not path_str:
        return None
    path = Path(path_str)
    if not path.exists():
        return None
    mime, _ = mimetypes.guess_type(str(path))
    mime = mime or "image/jpeg"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def _esc(value: Any) -> str:
    """HTML-Escaping mit Fallback auf Gedankenstrich."""
    text = str(value).strip() if value else ""
    return html.escape(text) if text else "—"


def _info_box(title: str, rows: list[tuple[str, str]]) -> str:
    """Rendert eine Daten-Box (Titelbalken + Label/Wert-Tabelle)."""
    cells = "".join(
        f'<tr><td class="label">{html.escape(label)}</td><td>{_esc(value)}</td></tr>'
        for label, value in rows
    )
    return (
        f'<div class="box"><div class="box-title">{html.escape(title)}</div>'
        f"<table>{cells}</table></div>"
    )


def _defect_card(defect: dict[str, Any]) -> str:
    """Rendert eine Mängel-Karte."""
    bewertung = str(defect.get("bewertung", "")).strip()
    badge_cls = SEVERITY_CLASS.get(bewertung.lower(), "badge-default")

    detail_rows = [
        ("Bereich", defect.get("bereich", "")),
        ("Feststellung", defect.get("beschreibung", "")),
        ("Rechtsgrundlage", defect.get("rechtsgrundlage", "")),
        ("Maßnahme / Auflage", defect.get("massnahme", "")),
        ("Frist", defect.get("frist", "")),
    ]
    details = "".join(
        f"<p><strong>{html.escape(label)}:</strong> {html.escape(str(value))}</p>"
        for label, value in detail_rows
        if value
    )
    src = ""
    if defect.get("video_quelle"):
        src = f'<p class="src">Quelle: {html.escape(str(defect["video_quelle"]))}</p>'

    photo = ""
    uri = _img_data_uri(defect.get("foto", ""))
    if uri:
        caption = html.escape(defect.get("foto_text", "Belegfoto (Standbild aus Video)"))
        photo = (
            f'<div class="photo"><img src="{uri}" alt="Belegfoto">'
            f'<div class="caption">{caption}</div></div>'
        )

    badge = ""
    if bewertung:
        badge = f'<span class="badge {badge_cls}">{html.escape(bewertung.upper())}</span>'

    return (
        '<div class="card"><div class="text">'
        f'<h3>Nr. {_esc(defect.get("nr"))} – {html.escape(str(defect.get("titel", "")))}</h3>'
        f"{badge}{details}{src}</div>{photo}</div>"
    )


def build_html(data: dict[str, Any]) -> str:
    """Baut das vollständige HTML-Dokument als String."""
    behoerde = data.get("behoerde", {})
    auth_lines = [
        f'<strong>{html.escape(behoerde.get("name", "Behörde / Dienststelle"))}</strong>',
        html.escape(behoerde.get("dienststelle", "")),
        html.escape(behoerde.get("anschrift", "")),
        html.escape(behoerde.get("kontakt", "")),
    ]
    auth_html = "<br>".join(line for line in auth_lines if line and line != "—")

    logo_html = ""
    logo_uri = _img_data_uri(behoerde.get("logo", "") or "")
    if logo_uri:
        logo_html = f'<img src="{logo_uri}" alt="Logo">'

    betrieb = data.get("betrieb", {})
    kontrolle = data.get("kontrolle", {})
    kontrolleur = data.get("kontrolleur", {})

    betrieb_box = _info_box("Betriebsdaten", [
        ("Betrieb", betrieb.get("name", "")),
        ("Inhaber/Verantw.", betrieb.get("inhaber", "")),
        ("Anschrift", betrieb.get("anschrift", "")),
        ("Betriebsart", betrieb.get("betriebsart", "")),
        ("Registriernr.", betrieb.get("registriernummer", "")),
    ])
    kontrolle_box = _info_box("Kontrolldaten", [
        ("Datum", kontrolle.get("datum", "")),
        ("Uhrzeit", kontrolle.get("uhrzeit", "")),
        ("Anlass", kontrolle.get("anlass", "")),
        ("Kontrolleur/in", kontrolleur.get("name", "")),
        ("Anwesend", kontrolle.get("anwesend", "")),
    ])

    maengel = data.get("maengel", [])
    anzahl = len(maengel)
    if maengel:
        cards = "".join(_defect_card(d) for d in maengel)
    else:
        cards = "<p>Bei der Kontrolle wurden keine Mängel festgestellt.</p>"

    summary = ""
    if data.get("gesamtbewertung") or data.get("naechste_schritte"):
        parts = ['<h2>Gesamtbewertung &amp; weiteres Vorgehen</h2><div class="summary">']
        if data.get("gesamtbewertung"):
            parts.append(f"<p>{html.escape(data['gesamtbewertung'])}</p>")
        if data.get("naechste_schritte"):
            parts.append(
                f"<p><strong>Nächste Schritte:</strong> "
                f"{html.escape(data['naechste_schritte'])}</p>"
            )
        parts.append("</div>")
        summary = "".join(parts)

    erstellt = datetime.now().strftime("%d.%m.%Y %H:%M")
    titel = html.escape(data.get("titel", "Kontrollbericht – Lebensmittelüberwachung"))
    untertitel = html.escape(
        data.get("untertitel", "Bericht über die amtliche Kontrolle gemäß VO (EU) 2017/625")
    )
    footer = (
        f"{html.escape(behoerde.get('name', ''))} · "
        f"Betrieb: {html.escape(betrieb.get('name', ''))}"
    )

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titel}</title>
<style>{CSS}</style>
</head>
<body>
<div class="page">
  <div class="head">
    <div class="authority">{auth_html}</div>
    <div>{logo_html}</div>
  </div>
  <div class="rule"></div>
  <h1>{titel}</h1>
  <p class="subtitle">{untertitel}</p>
  <div class="boxes">{betrieb_box}{kontrolle_box}</div>
  <h2>Mängelliste ({anzahl} Feststellung{"en" if anzahl != 1 else ""})</h2>
  {cards}
  {summary}
  <div class="signatures">
    <div class="sig">Ort, Datum</div>
    <div class="sig">Unterschrift Kontrolleur/in</div>
  </div>
  <p class="disclaimer">Automatisch erstellter Entwurf – {erstellt} Uhr.
    Standbilder wurden aus den vom Kontrolleur bereitgestellten Videos extrahiert.</p>
  <div class="footer">{footer}</div>
</div>
</body>
</html>
"""


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Lebensmittelkontroll-Bericht als HTML erstellen."
    )
    parser.add_argument("data", type=Path, help="JSON-Datei mit den Berichtsdaten")
    parser.add_argument(
        "--out", type=Path, default=Path("output/kontrollbericht.html"),
        help="Zielpfad für die HTML-Datei",
    )
    args = parser.parse_args()

    with args.data.open(encoding="utf-8") as fh:
        data = json.load(fh)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(build_html(data), encoding="utf-8")
    print(f"HTML-Bericht erstellt: {args.out}")


if __name__ == "__main__":
    main()
