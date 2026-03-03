# Hotel Aquarius – Gesamtprojekt

## Überblick
Dieses Repository enthält alle digitalen Systeme des **Hotel Aquarius** (54 Zimmer) in Norddeich, Ostfriesland an der Nordsee. Es umfasst das bestehende VBA-basierte Buchungsmanagement, neue Python/AI-Module für Automatisierung und Revenue Management sowie Web-Komponenten.

## Projektstruktur

```
hotel-aquarius/
├── CLAUDE.md                  # Diese Datei
├── README.md                  # Projektdokumentation
│
├── vba/                       # Excel/VBA Buchungssystem
│   ├── CLAUDE.md              # VBA-spezifische Anweisungen
│   ├── buchungssystem.xlsm    # Haupt-Buchungsdatei
│   ├── modules/               # Exportierte VBA-Module (.bas)
│   ├── forms/                 # UserForms (.frm)
│   └── docs/                  # Dokumentation der VBA-Logik
│
├── python/                    # Python/AI-Module
│   ├── CLAUDE.md              # Python-spezifische Anweisungen
│   ├── requirements.txt
│   ├── revenue_management/    # Preisoptimierung & Konkurrenzanalyse
│   ├── auswertungen/          # Monatsberichte, Statistiken
│   ├── automation/            # Workflow-Automatisierung
│   └── tests/
│
├── web/                       # Webseite & Online-Komponenten
│   ├── CLAUDE.md              # Web-spezifische Anweisungen
│   ├── index.html
│   ├── css/
│   ├── js/
│   └── assets/
│
├── data/                      # Daten & Konfiguration (NICHT in Git!)
│   └── .gitkeep
│
├── docs/                      # Übergreifende Dokumentation
│   ├── architektur.md
│   └── workflows.md
│
└── .gitignore
```

## Tech-Stack

| Bereich | Technologie | Zweck |
|---------|-------------|-------|
| Buchungssystem | Excel / VBA | Kernbuchungsverwaltung, Tagesübersichten, Monatsauswertungen |
| AI & Automatisierung | Python 3.11+ | Revenue Management, Preisoptimierung, Datenanalyse |
| Web | HTML / CSS / JavaScript | Webseite, ggf. Online-Buchungsformulare |
| Datenquellen | OTA Insight, Booking.com | Konkurrenzpreise, Marktdaten |
| Voice AI | ElevenLabs (geplant) | Telefonische Gästebetreuung, mehrsprachig |

## Geschäftskontext

- **Standort:** Norddeich, Ostfriesland (Nordseeküste)
- **Kapazität:** 54 Zimmer
- **Saison:** Starke saisonale Schwankungen (Hochsaison Sommer, Nebensaison Winter)
- **Zielgruppe:** Nordsee-Urlauber, Familien, Kurz-/Langzeitgäste
- **Restaurant:** Eigenes Hotelrestaurant mit wechselnder Speisekarte

## Konventionen

### Allgemein
- **Sprache im Code:** Englische Variablen- und Funktionsnamen
- **Kommentare:** Deutsch (da Ein-Personen-Projekt)
- **Commit-Messages:** Deutsch, im Format: `[bereich] Beschreibung` (z.B. `[vba] Monatsauswertung optimiert`)
- **Sensible Daten:** Niemals Gästedaten, Passwörter oder API-Keys committen

### VBA
- Modulnamen mit Präfix: `mod_`, `frm_`, `cls_`
- Option Explicit in jedem Modul
- Fehlerbehandlung mit `On Error GoTo`
- VBA-Module als `.bas`-Dateien exportieren für Versionskontrolle

### Python
- PEP 8 Style Guide
- Type Hints verwenden
- Docstrings in Google-Style (Deutsch)
- Virtual Environment: `venv/` (in .gitignore)
- Pandas für Datenverarbeitung, openpyxl für Excel-Integration

### Web
- Kein Framework-Zwang – Vanilla JS bevorzugt für einfache Seiten
- Responsive Design (Mobile First)
- Barrierefreiheit beachten (WCAG 2.1 AA)

## Wichtige Auswertungslogik

Die monatliche Auswertung folgt dieser Logik:
- **Roomnights:** Anzahl belegter Zimmer pro Nacht
- **Ankünfte:** Summe der anreisenden **Personen** (nicht Zimmer!)
- **Übernachtungen:** Gesamtzahl aller Gästeübernachtungen
- **Excel-Ausgabe:** Zusammenfassung + Tagesübersicht (Datum, Wochentag, Ankünfte, Belegte Zimmer, Übernachtungen)
- **Formatierung:** Wochenenden farbig hervorheben, Summen und Durchschnitte am Ende

## Schnittstellen

```
Excel/VBA (Buchungssystem)
    ↕ openpyxl / xlwings
Python (AI-Module)
    ↕ API-Calls
Externe Dienste (OTA Insight, ElevenLabs)
```

## Lokale Entwicklung

```bash
# Repository initialisieren
git init hotel-aquarius
cd hotel-aquarius

# Python-Umgebung einrichten
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
pip install -r python/requirements.txt

# VBA-Module: manuell in Excel importieren
```

## Offene Ziele / Roadmap

- [ ] Revenue Management System (Konkurrenzpreise analysieren, Preisempfehlungen)
- [ ] Automatisierte Monatsauswertungen aus Buchungsliste
- [ ] ElevenLabs Voice AI für Telefonannahme
- [ ] Integration Claude API für Gästekommunikation
- [ ] Webseite mit Buchungsformular
- [ ] Thunderbird-Addon: E-Mail → Excel Workflow
