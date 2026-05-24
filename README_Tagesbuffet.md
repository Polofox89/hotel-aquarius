# Tagesbuffet-Generator – Hotel Aquarius

Automatische Erstellung von Tagesbuffet-Menübildern (1080×1920 px) und Excel-Archivierung.

## Voraussetzungen

```bash
pip install Pillow openpyxl
# Optional für Spracheingabe:
pip install SpeechRecognition pyaudio
```

## Verwendung

### Interaktiver Modus (Standard)
```bash
python tagesbuffet_generator.py
```

### Spracheingabe
```bash
python tagesbuffet_generator.py --voice
```

### Eigene Pfade
```bash
python tagesbuffet_generator.py \
  --logo   ./Logo_JPG.jpg \
  --output ./output/
```

### Über Umgebungsvariablen
```bash
export BUFFET_LOGO=/pfad/zum/logo.jpg
export BUFFET_OUTPUT=/pfad/zur/ausgabe/
python tagesbuffet_generator.py
```

## Ablauf

```
1. Datum eingeben (Enter = heute)
2. Speisen pro Kategorie eingeben
3. Menü bestätigen
→ Bild wird gespeichert
→ Excel-Archiv wird aktualisiert
```

## Ausgabe

| Datei | Beschreibung |
|-------|-------------|
| `tagesbuffet_DD_MM_YYYY.jpg` | Menübild (1080×1920 px) |
| `Tagesbuffet_Archiv.xlsx` | Excel-Archiv aller Menüs |

## Menü-Kategorien

| Kategorie | Gerichte | Standard |
|-----------|----------|---------|
| Suppe | 1 | – |
| Hauptgerichte | 2–3 | – |
| Beilagen | 3–4 | Gemüse zuerst, dann Stärke |
| Salate | 1 | Salatbuffet |
| Partypfanne | 1 | – |
| Dessert | 1 | Dessertbuffet |

## Bildgestaltung

- **Format:** 1080×1920 px, JPEG (Qualität 95)
- **Hintergrund:** Weiß
- **Logo:** Zentriert oben, 450 px breit
- **Inhalt:** Vertikal und horizontal zentriert
- **Farben:** `#2c2c2c` Text · `#666666` Datum · `#999999` Labels · `#cccccc` Linien

## Excel-Archiv

Spalten: **Datum** | **Kategorie** | **Speise**

- Header: Dunkelblau (`#0d4f6b`) mit weißer Schrift
- Alternierende Zeilen: Hellblau (`#e8f4f8`)
- Wird bei jedem neuen Menü automatisch erweitert

## Hinweise

- Das Logo wird exakt **einmal** eingefügt (obere Bildmitte)
- Fehlende Schriftarten → automatischer Fallback auf PIL-Standard
- Fehlendes Logo → Bild wird ohne Logo erstellt (Warnung im Terminal)
- Beschädigtes Excel-Archiv → automatische Neuerstellung
