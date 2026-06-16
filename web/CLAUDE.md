# Web – Hotel Aquarius

Web-Komponenten des Hotels (Vanilla HTML/CSS/JS, kein Framework-Zwang).

## Konventionen
- Mobile First, responsive
- Barrierefreiheit beachten (WCAG 2.1 AA): Fokus-Stile, `aria`-Attribute, Tastaturbedienung
- Englische Bezeichner im Code, deutsche Kommentare
- Keine externen Abhängigkeiten ohne triftigen Grund

## Komponenten

### Timer (`index.html`, `css/timer.css`, `js/timer.js`)
Großflächiger Timer für den Hotelbetrieb (z. B. Küche/Restaurant, Veranstaltungen).

- **Analog & digital:** SVG-Zifferblatt mit ablaufendem Fortschrittsbogen und
  sweependem Zeiger, dazu mittige Digitalanzeige (`MM:SS`, ab 1 h `HH:MM:SS`).
- **Sekundengenau einstellbar** über Stunden/Minuten/Sekunden-Felder oder Presets.
- **Voreinstellung:** 10 Minuten.
- **Ping** alle 30 Sekunden (dezenter Sinus-Ton).
- **Jingle** beim Erreichen von Null (kurze Melodie + Akkord).
- **Vollbild**-Modus für großflächige Darstellung; Leertaste = Start/Pause; Ton stummschaltbar.

Audio wird über die **Web Audio API** erzeugt – es sind keine Audiodateien nötig.
Die verbleibende Zeit wird aus `performance.now()` berechnet (driftfrei).

Reine statische Seite: einfach `web/index.html` im Browser öffnen.
