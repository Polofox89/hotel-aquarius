---
name: lebensmittelkontroll-bericht
description: >-
  Erstellt aus kurzen Inspektions-Videos (plus Kommentaren des Kontrolleurs)
  einen sauber formatierten Lebensmittelkontroll-/Mängelbericht als PDF.
  Nutzen, wenn der/die Nutzer:in einen Kontrollbericht, Mängelbericht oder
  Inspektionsbericht für einen Lebensmittelbetrieb erstellen möchte – mit
  Belegfotos aus Videos, Mängelliste, Bewertung und Fristen. Stichworte:
  Lebensmittelkontrolle, Hygienekontrolle, Mängelliste, Betriebskontrolle,
  Kontrollbericht PDF.
---

# Lebensmittelkontroll-Bericht (PDF)

Erzeugt einen amtlich anmutenden PDF-Bericht für die Lebensmittelüberwachung:
Kopfzeile, Betriebs- und Kontrolldaten, Mängelliste als Karten mit Belegfoto und
farbigem Bewertungs-Badge, Gesamtbewertung und Unterschriftenzeile.

Die Skript-Basis liegt in `python/lebensmittelkontrolle/` (Single Source of
Truth): `extract_frame.py` (Standbild aus Video) und `generate_report.py`
(PDF aus JSON). Vorlage: `report_data.example.json`.

## Wichtige Grenze (immer beachten)

Du kannst **den Bild-/Toninhalt von Videos nicht automatisch auswerten**. Die
inhaltlichen Mängelbeschreibungen stammen aus den **Kommentaren des Kontrolleurs**.
Aus jedem Video wird lediglich **ein Standbild** als Belegfoto extrahiert. Du
darfst das extrahierte Standbild (ein Einzelbild) ansehen und beschreiben und
daraus einen Formulierungs-**Vorschlag** machen – aber als Vorschlag kennzeichnen
und vom Nutzer bestätigen lassen.

## Voraussetzungen

```bash
pip install -r python/lebensmittelkontrolle/requirements.txt
```
(reportlab, Pillow, imageio-ffmpeg – portables ffmpeg, keine Systeminstallation.)

## Ablauf

1. **Videos entgegennehmen.** Hochgeladene Videodateien nach
   `python/lebensmittelkontrolle/media/` kopieren (sprechende Namen, z. B.
   `video1_<zeit>.mp4`).

2. **Pro Video ein Standbild extrahieren** (Standard = Mitte des Videos):
   ```bash
   cd python/lebensmittelkontrolle
   python extract_frame.py media/video1_xxxx.mp4 media/frame_1.jpg
   # optionaler Zeitpunkt in Sekunden: --zeit 4
   ```
   Das erzeugte `frame_N.jpg` ansehen, kurz beschreiben und dem Nutzer je Video
   einen Formulierungsvorschlag für die Feststellung anbieten.

3. **Kopfdaten klären.** Behörde/Dienststelle, Kontrolleur:in, Betrieb
   (Name, Inhaber, Anschrift, Betriebsart, Registriernr.) und Kontrolldaten
   (Datum, Uhrzeit, Anlass, Anwesende). Liegen sie nicht vor und ist es ein
   Probelauf, eckige Platzhalter wie `[Betriebsname]` verwenden.

4. **`report_data.json` erstellen.** `report_data.example.json` als Struktur
   nehmen. Pro Mangel: `nr`, `titel`, `bereich`, `beschreibung` (= bestätigter
   Kommentar), `bewertung` (`geringfügig` | `erheblich` | `gravierend`),
   `rechtsgrundlage`, `massnahme`, `frist`, `foto` (Pfad zum Standbild),
   `foto_text`, `video_quelle`.

5. **PDF erzeugen:**
   ```bash
   python generate_report.py report_data.json --out output/kontrollbericht.pdf
   ```

6. **Ausliefern.** Das PDF dem Nutzer schicken (SendUserFile). Eine PNG-Vorschau
   pro Seite kann vorab zur Abnahme gerendert werden (z. B. mit pymupdf).

## Bewertungsstufen → Badge-Farbe

| Wert          | Farbe  |
|---------------|--------|
| `geringfügig` | grün   |
| `erheblich`   | orange |
| `gravierend`  | rot    |

## Datenschutz

`media/`, `output/` und `report_data.json` enthalten vertrauliche Betriebs-/
Personendaten und sind per `.gitignore` von der Versionierung ausgeschlossen.
Niemals reale Inhalte committen – nur Code und Vorlage (`*.example.json`).
