#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tagesbuffet Web-App – Hotel Aquarius
=====================================
FastAPI-Backend, das den vorhandenen TagesbuffetGenerator als Web-Service
anbietet. Frontend liegt unter ./static/index.html (HTML + Vanilla JS).

Start (lokal):
    uvicorn web_app:app --reload --port 8000

Produktion (auf VPS):
    siehe systemd-Service tagesbuffet.service

Umgebungsvariablen
------------------
BUFFET_DATA         Verzeichnis für Bilder + Excel (default: ./data)
ANTHROPIC_API_KEY   Für KI-Analyse (optional – fehlt sie, ist /api/analyze deaktiviert)
"""

from __future__ import annotations

import os
import json
from datetime import datetime, date as date_cls
from io import BytesIO
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from tagesbuffet_generator import TagesbuffetGenerator, CATEGORIES
from buffet_core import (
    build_suggestions_from_excel,
    ki_kategorisieren,
    SLOTS,
    DEFAULT_SUGGESTIONS,
    ANTHROPIC_OK,
)


# ── Pfade ─────────────────────────────────────────────────────────────────────

DATA_DIR    = Path(os.getenv("BUFFET_DATA", str(Path(__file__).parent / "data")))
IMAGES_DIR  = DATA_DIR / "images"
ARCHIV_DIR  = DATA_DIR / "archiv"
HISTORY_FILE = DATA_DIR / "history.json"

for d in (DATA_DIR, IMAGES_DIR, ARCHIV_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Generator – nutzt die konfigurierten Pfade
generator = TagesbuffetGenerator(image_dir=IMAGES_DIR, archiv_dir=ARCHIV_DIR)


# ── Pydantic-Modelle ──────────────────────────────────────────────────────────

class MenuPayload(BaseModel):
    """Datum (ISO) + Menü (Kategorie-Key → Liste von Speisen)."""
    date: str = Field(..., examples=["2026-05-25"])
    menu: dict = Field(..., examples=[{
        "suppe":      ["Tomatensuppe"],
        "haupt":      ["Wiener Schnitzel", "Lachsfilet"],
        "pasta":      ["Spaghetti Bolognese"],
        "beilagen":   ["Bratkartoffeln", "Reis", "Brokkoli"],
        "salate":     ["Salatbuffet"],
        "partypfanne":["Tagesempfehlung"],
        "dessert":    ["Dessertbuffet"],
    }])


class AnalyzeRequest(BaseModel):
    text: str


# ── FastAPI-App ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Tagesbuffet API",
    description="Hotel Aquarius · Norddeich – Tagesbuffet-Generator",
    version="1.0.0",
)

# CORS für lokale Entwicklung erlauben
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Statische Frontend-Dateien
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ── Routen: Frontend ──────────────────────────────────────────────────────────

def _asset_version(filename: str) -> str:
    """Versions-Stempel = mtime der Datei. Ändert sich bei jedem Deploy."""
    try:
        return str(int((STATIC_DIR / filename).stat().st_mtime))
    except OSError:
        return "0"


@app.get("/", response_class=HTMLResponse)
async def index():
    """Liefert das Frontend (index.html) mit Cache-Busting-Versionen."""
    html_path = STATIC_DIR / "index.html"
    if not html_path.exists():
        return HTMLResponse(
            "<h1>Tagesbuffet API läuft ✓</h1>"
            "<p>Aber kein <code>static/index.html</code> gefunden.</p>",
            status_code=200,
        )
    html = html_path.read_text(encoding="utf-8")
    # Cache-Busting: ?v=<mtime> an jede lokale JS/CSS-URL hängen
    for fn in ("style.css", "i18n.js", "app.js"):
        html = html.replace(
            f"/static/{fn}",
            f"/static/{fn}?v={_asset_version(fn)}",
        )
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})


# ── Routen: Metadaten ─────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "image_dir":   str(IMAGES_DIR),
        "archiv_dir":  str(ARCHIV_DIR),
        "ki_available": bool(ANTHROPIC_OK and os.getenv("ANTHROPIC_API_KEY")),
    }


@app.get("/api/categories")
async def get_categories():
    """Kategorien und Slot-Definitionen für das Frontend."""
    cats = [
        {"key": k, "label": label, "min": mn, "max": mx, "defaults": defaults}
        for k, label, mn, mx, defaults in CATEGORIES
    ]
    slots = [
        {"slot": s, "category": c, "index": idx, "label_key": lk, "optional": opt}
        for s, c, idx, lk, opt in SLOTS
    ]
    return {"categories": cats, "slots": slots}


@app.get("/api/suggestions")
async def get_suggestions():
    """Alle bisher verwendeten Gerichte pro Kategorie (aus Excel-Archiv + Defaults)."""
    archiv_file = ARCHIV_DIR / "Tagesbuffet_Archiv.xlsx"
    return build_suggestions_from_excel(archiv_file)


# ── Routen: Live-Vorschau ─────────────────────────────────────────────────────

@app.post("/api/preview")
async def preview(payload: MenuPayload):
    """Rendert ein Vorschaubild (JPEG, in-memory, ohne Speichern)."""
    try:
        d = datetime.fromisoformat(payload.date)
    except ValueError:
        raise HTTPException(400, f"Ungültiges Datum: {payload.date}")

    try:
        img = generator.render_image(d, payload.menu)
    except Exception as e:
        raise HTTPException(500, f"Render-Fehler: {e}")

    buf = BytesIO()
    img.save(buf, "JPEG", quality=82, optimize=True)
    buf.seek(0)
    return Response(
        content=buf.read(),
        media_type="image/jpeg",
        headers={"Cache-Control": "no-store"},
    )


# ── Routen: Speichern ─────────────────────────────────────────────────────────

@app.post("/api/save")
async def save(payload: MenuPayload):
    """Speichert Bild auf Platte + aktualisiert Excel-Archiv + History."""
    try:
        d = datetime.fromisoformat(payload.date)
    except ValueError:
        raise HTTPException(400, f"Ungültiges Datum: {payload.date}")

    img_path = generator.create_image(d, payload.menu)
    try:
        generator.update_excel(d, payload.menu)
    except Exception as e:
        # Excel-Fehler ist nicht fatal – Bild bleibt gespeichert
        print(f"Warnung: Excel-Update fehlgeschlagen: {e}")

    _add_to_history(d, payload.menu)

    return {
        "saved": img_path.name,
        "url": f"/api/images/{img_path.name}",
        "date": d.isoformat(),
    }


# ── Routen: KI-Analyse ────────────────────────────────────────────────────────

@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest):
    """Schickt Freitext an Claude und liefert kategorisiertes Menü zurück."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or not ANTHROPIC_OK:
        raise HTTPException(
            503,
            "KI-Analyse nicht verfügbar – ANTHROPIC_API_KEY fehlt oder anthropic-Paket "
            "nicht installiert."
        )
    if not req.text.strip():
        raise HTTPException(400, "Eingabetext leer.")
    try:
        menu = ki_kategorisieren(req.text, api_key)
    except Exception as e:
        raise HTTPException(500, f"KI-Fehler: {e}")
    return {"menu": menu}


# ── Routen: Bilder ────────────────────────────────────────────────────────────

@app.get("/api/images/{filename}")
async def get_image(filename: str):
    """Liefert ein gespeichertes Bild aus dem Daten-Ordner."""
    # Pfad-Traversal-Schutz
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(400, "Ungültiger Dateiname.")
    file = IMAGES_DIR / filename
    if not file.exists():
        raise HTTPException(404, "Bild nicht gefunden.")
    return FileResponse(str(file), media_type="image/jpeg")


@app.get("/api/latest")
async def get_latest_image_info():
    """Info zum neuesten Bild – für /display Auto-Polling."""
    files = sorted(
        IMAGES_DIR.glob("tagesbuffet_*.jpg"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not files:
        return {"name": None, "url": None, "mtime": None}
    f = files[0]
    return {
        "name":  f.name,
        "url":   f"/api/images/{f.name}",
        "mtime": f.stat().st_mtime,
    }


@app.get("/display", response_class=HTMLResponse)
async def display():
    """
    Vollbild-Anzeige des neuesten Tagesbuffet-Bildes.
    Speziell für Fire TV / TV-Bildschirme.
    Pollt jede Minute nach Updates, schwarzer Hintergrund, keine UI.
    """
    return HTMLResponse("""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tagesbuffet · Hotel Aquarius</title>
<style>
  html, body { margin: 0; padding: 0; height: 100%; background: #000;
               overflow: hidden; font-family: system-ui, sans-serif; }
  #wrap { width: 100vw; height: 100vh;
          display: flex; align-items: center; justify-content: center; }
  img { max-width: 100%; max-height: 100%; object-fit: contain; }
  #placeholder { color: #888; font-size: 1.5em; text-align: center; }
  #placeholder .small { font-size: 0.6em; color: #444; display: block; margin-top: 1em; }
</style>
</head>
<body>
  <div id="wrap">
    <div id="placeholder">
      Noch kein Tagesbuffet gespeichert.
      <span class="small">Im Admin-Bereich speichern, dann erscheint es hier automatisch.</span>
    </div>
  </div>
<script>
let currentMtime = null;
async function poll() {
  try {
    const r = await fetch('/api/latest', { cache: 'no-store' });
    if (!r.ok) return;
    const data = await r.json();
    if (data.url && data.mtime !== currentMtime) {
      currentMtime = data.mtime;
      const wrap = document.getElementById('wrap');
      // Cache-Buster anhängen, damit Browser garantiert die neue Datei holt
      wrap.innerHTML = '<img src="' + data.url + '?t=' + Date.now() + '" alt="Tagesbuffet" />';
    }
  } catch (e) { /* still polling */ }
}
poll();
setInterval(poll, 60000);  // jede Minute prüfen
</script>
</body>
</html>""")


@app.get("/api/images")
async def list_images():
    """Liste aller gespeicherten Bilder, neueste zuerst."""
    files = sorted(
        IMAGES_DIR.glob("tagesbuffet_*.jpg"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return [
        {"name": f.name, "url": f"/api/images/{f.name}", "mtime": f.stat().st_mtime}
        for f in files
    ]


# ── Routen: Verlauf ───────────────────────────────────────────────────────────

WEEKDAYS_DE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag",
               "Freitag", "Samstag", "Sonntag"]


def _read_history() -> list:
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _add_to_history(d: datetime, menu: dict) -> None:
    history = _read_history()
    entry = {
        "date":    d.strftime("%d.%m.%Y"),
        "weekday": WEEKDAYS_DE[d.weekday()],
        "menu":    menu,
    }
    # Duplikat (gleicher Tag) entfernen
    history = [h for h in history if h.get("date") != entry["date"]]
    history.insert(0, entry)
    history = history[:30]  # max 30 Einträge
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Warnung: History konnte nicht geschrieben werden: {e}")


@app.get("/api/history")
async def get_history(limit: int = 7):
    """Letzte gespeicherte Menüs (default 7 Tage)."""
    return _read_history()[:max(1, min(limit, 30))]


# ── Lokaler Start ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web_app:app", host="0.0.0.0", port=8000, reload=True)
