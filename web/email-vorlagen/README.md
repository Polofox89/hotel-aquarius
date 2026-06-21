# E-Mail-Vorlagen für Gäste-Antworten

Dieses Verzeichnis enthält die Standard-Vorlage für Antwort-E-Mails an Gäste des
Hotel Aquarius. Das Design entspricht den gesendeten Buchungsbestätigungen
(Logo oben, Arial, feste Signatur).

## Dateien

| Datei | Zweck |
|-------|-------|
| `gast-antwort-vorlage.html` | HTML-Grundgerüst mit Platzhaltern |
| `logo-aquarius.b64` | Base64-kodiertes Hotel-Logo (in `{{LOGO_BASE64}}` einsetzen) |

## Platzhalter

| Platzhalter | Beispiel |
|-------------|----------|
| `{{LOGO_BASE64}}` | Inhalt aus `logo-aquarius.b64` |
| `{{EMPFAENGER}}` | `Herr Markus Buschmann` |
| `{{DATUM}}` | `21.06.2026` |
| `{{ANREDE}}` | `sehr geehrter Herr Buschmann` |
| `{{INHALT}}` | Ein oder mehrere `<p>…</p>`-Absätze mit der eigentlichen Antwort |

## Stil-Konventionen

- Begrüßung: **„Moin moin, {{ANREDE}},"**
- Abschluss: **„Mit freundlichen Grüßen"** / **Axel Grüttner**
- Signatur (fest): Alter Dörper Weg 20, 26506 Norddeich Ostf., Tel.: 04931/93230,
  www.hotel-aquarius-norddeich.de
- Inhaltliche Angaben (Check-in, Preise, Ausstattung) immer mit den offiziellen
  FAQ abgleichen: https://hotel-aquarius-norddeich.de/faq

## Wichtige Hotel-Eckdaten (Stand FAQ)

- **Check-in** ab 15 Uhr (früher anreisen / parken / Gepäck deponieren möglich)
- **Check-out** bis 11 Uhr (Verlängerung gegen 15 € Aufpreis)
- **Frühstück** 7–10 Uhr (im Winter ab 8 Uhr)
- **Abendessen** 17:45–19:15 Uhr (Buffet); Halbpension Plus inkl. Getränke
- Halbpension nachträglich an der Rezeption: 27,50 € p. P.
- **Pool** 10–21 Uhr; **Sauna & Whirlpool** 16–21 Uhr
- Bademantel-Leihgebühr einmalig 4 €, Extra-Badehandtuch 1 €
- **Kostenlose Parkplätze** direkt vor dem Hotel
- **Überdachter Abstellbereich für Fahrräder**
- Entfernung zum Deich zu Fuß ca. 15 min
- **Hunde** auf Anfrage: 1. Hund 15 €/Nacht, 2 Hunde 40 €/Nacht; nur im
  Terrassenzimmer; im Speiseraum (Extra-Raum) erlaubt
- **Stornobedingungen:** bis 4 Wochen vorher kostenfrei, bis 1 Woche vorher 40 %,
  bis 1 Tag vorher 60 %, bei Nichtanreise 80 %
