#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test-Skript für den Tagesbuffet-Generator.
Ruft den Generator direkt mit Beispieldaten auf (kein interaktiver Modus).
"""

import sys
from pathlib import Path
from datetime import datetime

# Pfad zum Generator
sys.path.insert(0, str(Path(__file__).parent))

# Ausgabe ins lokale test_output/
import tagesbuffet_generator as gen

gen.OUTPUT_DIR  = Path(__file__).parent.parent.parent / "test_output"
gen.ARCHIV_FILE = gen.OUTPUT_DIR / "Tagesbuffet_Archiv.xlsx"
gen.LOGO_PATH   = Path("/mnt/user-data/uploads/Logo_JPG.jpg")  # Wird ohne Logo erstellt

# Heutiges Datum
today = datetime.today()

# Beispiel-Menü (Dienstag, 03.03.2026)
beispiel_menu = {
    "suppe":       ["Hausgemachte Tomatensuppe"],
    "haupt":       ["Schweinebraten mit Soße", "Gebratene Hähnchenbrust"],
    "beilagen":    ["Gedünstetes Saisongemüse", "Rotkohl", "Salzkartoffeln"],
    "salate":      ["Salatbuffet"],
    "partypfanne": ["Gemischte Grillpfanne"],
    "dessert":     ["Dessertbuffet"],
}

generator = gen.TagesbuffetGenerator()

print("=" * 52)
print("  TEST – Tagesbuffet-Generator")
print("=" * 52)
print(f"  Datum:   {generator.format_date_de(today)}")
print(f"  Ausgabe: {gen.OUTPUT_DIR}")
print()

# Bild erstellen
print("  [1/2] Erstelle Bild ...")
img_path = generator.create_image(today, beispiel_menu)

# Excel aktualisieren
print("  [2/2] Excel-Archiv ...")
generator.update_excel(today, beispiel_menu)

print()
print("  Ergebnis:")
print(f"    Bild:   {img_path}")
print(f"    Archiv: {gen.ARCHIV_FILE}")
print()

# Dateigröße ausgeben
if img_path.exists():
    kb = img_path.stat().st_size // 1024
    print(f"    Bildgröße: {kb} KB")
if gen.ARCHIV_FILE.exists():
    kb = gen.ARCHIV_FILE.stat().st_size // 1024
    print(f"    Excel-Größe: {kb} KB")
