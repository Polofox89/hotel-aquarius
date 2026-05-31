# Stundenzettel-Auswertung

Berechnet aus den fotografierten Mitarbeiter-Stundenzetteln die monatliche
Arbeitszeit und schreibt sie in eine gemeinsame Excel-Datei
(`stundenauswertung.xlsx`).

## Berechnungslogik

```
Netto-Arbeitszeit pro Tag = (bis − von) − Pause
```

- Die Pause wird **so angesetzt, wie auf dem Zettel eingetragen**.
- Ist **keine** Pause eingetragen, werden pauschal **30 Minuten** abgezogen
  (`STANDARD_PAUSE_MIN`).
- Alle Zeiten werden im Format **Stunden:Minuten** ausgegeben (z. B. `7:30`).

## Dateien

| Datei | Zweck |
|-------|-------|
| `stundenzettel_auswertung.py` | Datenmodell + Excel-Erzeugung (Logik) |
| `daten_mai_2026.py` | Abgelesene Tagesdaten je Mitarbeiter für Mai 2026 |
| `stundenauswertung.xlsx` | Erzeugte Excel-Auswertung (Ergebnis) |

## Excel-Aufbau

- **Übersicht** (erstes Blatt): Mitarbeiter, Monat, Arbeitstage, Gesamtstunden.
- **Ein Blatt je Mitarbeiter**: Tagesübersicht mit Datum, Wochentag, von, bis,
  Pause, Stunden – Wochenenden farbig hervorgehoben, freie Tage grau,
  Summenzeile am Ende.

## Verwendung

```bash
cd python/auswertungen
python3 daten_mai_2026.py
```

Neue Monate/Mitarbeiter: eine analoge Datendatei anlegen (oder die bestehende
ergänzen) und `schreibe_auswertung([...])` aufrufen. Bereits gespeicherte
Mitarbeiterblätter bleiben erhalten, gleichnamige Blätter werden aktualisiert.

## Abhängigkeiten

```bash
pip install -r ../requirements.txt   # openpyxl
```

## Hinweis zur Datenerfassung

Die Tagesdaten werden manuell aus den Fotos der Stundenzettel übertragen.
Unsichere Ablesungen sind in der jeweiligen Datendatei als Kommentar markiert
und sollten vor der Lohnabrechnung gegengeprüft werden.
