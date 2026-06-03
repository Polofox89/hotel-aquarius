# Lebensmittelkontroll-Bericht (PDF)

Werkzeug zum Erstellen sauber formatierter **Kontrollberichte / Mängelberichte**
für die amtliche Lebensmittelüberwachung. Erzeugt ein mehrseitiges PDF mit
Kopfzeile, Betriebs- und Kontrolldaten, einer Mängelliste mit Belegfotos und
Bewertungs-Badges sowie Gesamtbewertung und Unterschriftenzeile.

Belegfotos können automatisch als **Standbild aus kurzen Videos** extrahiert
werden (portables `ffmpeg`, keine Systeminstallation nötig).

## Installation

```bash
pip install -r requirements.txt
```

## Workflow

1. **Videos/Fotos ablegen** – Videodateien in `media/` legen.
2. **Standbild je Video extrahieren** (1 Bild pro Video, Standard = Mitte):
   ```bash
   python extract_frame.py media/kuehlschrank.mp4 media/frame_1.jpg
   # optional Zeitpunkt in Sekunden:
   python extract_frame.py media/kuehlschrank.mp4 media/frame_1.jpg --zeit 4
   ```
3. **Berichtsdaten pflegen** – `report_data.example.json` kopieren und ausfüllen.
   Jeder Mangel erhält Titel, Bereich, Beschreibung (= dein Kommentar zum
   Video), Bewertung, Rechtsgrundlage, Maßnahme, Frist und das `foto`.
4. **PDF erzeugen:**
   ```bash
   python generate_report.py report_data.json --out output/kontrollbericht.pdf
   ```

## Bewertungsstufen (Farb-Badge)

| Wert          | Farbe  |
|---------------|--------|
| `geringfügig` | grün   |
| `erheblich`   | orange |
| `gravierend`  | rot    |

## Datenstruktur

Siehe `report_data.example.json`. Felder pro Mangel:

| Feld             | Bedeutung                                            |
|------------------|------------------------------------------------------|
| `nr`             | Laufende Nummer                                      |
| `titel`          | Kurztitel des Mangels                                |
| `bereich`        | Ort/Bereich (z. B. „Küche – Kühlung")               |
| `beschreibung`   | Feststellung (i. d. R. dein Video-Kommentar)        |
| `bewertung`      | `geringfügig` / `erheblich` / `gravierend`          |
| `rechtsgrundlage`| z. B. „VO (EG) 852/2004, Anh. II …"                 |
| `massnahme`      | Geforderte Maßnahme / Auflage                       |
| `frist`          | Frist zur Behebung                                  |
| `foto`           | Pfad zum Belegfoto (z. B. `media/frame_1.jpg`)      |
| `foto_text`      | Bildunterschrift                                    |
| `video_quelle`   | Herkunft (Dateiname + Zeitpunkt)                   |

## Datenschutz

Inhalte in `media/` und `output/` sind **vertraulich** und per `.gitignore`
vom Versionsmanagement ausgeschlossen. Niemals echte Betriebs-/Personendaten
committen.

## Hinweis zur Video-Auswertung

Die inhaltliche Beschreibung der Mängel stammt aus den **Kommentaren des
Kontrolleurs**; die Bild- und Tonspur der Videos wird nicht automatisch
inhaltlich ausgewertet. Aus jedem Video wird lediglich ein Standbild als
Belegfoto extrahiert.
