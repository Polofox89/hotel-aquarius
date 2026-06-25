# Slack – Funktion und Benutzung

Diese Erklärung dient als kurze Einführung in Slack für das Team des Hotel Aquarius.

## Was ist Slack?

**Slack** ist ein Messaging- und Kollaborationstool für Teams – vergleichbar mit
einem „WhatsApp für die Arbeit", aber deutlich strukturierter. Statt vieler
E-Mails kommuniziert das Team in thematisch sortierten Kanälen in Echtzeit.

## Wichtigste Funktionen

| Funktion | Erklärung |
|----------|-----------|
| **Channels (Kanäle)** | Themenräume, z. B. `#rezeption`, `#restaurant`, `#technik`. Jeder sieht nur, was ihn betrifft. |
| **Direktnachrichten (DMs)** | Private 1:1- oder Gruppen-Chats. |
| **Threads** | Antworten direkt an einer Nachricht – hält die Kanäle aufgeräumt. |
| **Dateien teilen** | Bilder, PDFs, Excel-Dateien per Drag & Drop. |
| **Suche** | Volltextsuche über alle Nachrichten und Dateien. |
| **Integrationen / Apps** | Verbindung zu anderen Diensten (Google Kalender, E-Mail, eigene Skripte). |
| **Benachrichtigungen** | Push auf Handy & Desktop, einstellbar pro Kanal. |
| **Huddles / Anrufe** | Schnelle Audio- und Video-Gespräche. |

## Benutzung – Schritt für Schritt

1. **Workspace beitreten:** Man tritt einem „Workspace" bei (z. B. „Hotel
   Aquarius"). Die Einladung kommt per E-Mail.
2. **App installieren:** Desktop (Windows/Mac), Handy (iOS/Android) oder im
   Browser nutzen.
3. **Kanal wählen** und Nachricht ins Textfeld unten tippen → Enter zum Senden.
4. **@Name** erwähnen, um jemanden gezielt zu benachrichtigen; **@channel** für
   alle im Kanal.
5. **Antworten:** Auf „In Thread antworten" klicken, um Diskussionen zu bündeln.

## Relevanz für Hotel Aquarius

Für ein 54-Zimmer-Haus kann Slack die Schichtkommunikation zwischen
**Rezeption, Restaurant und Housekeeping** bündeln. Interessant ist außerdem
eine **Integration mit den Python-Modulen** dieses Projekts:

- Automatische Benachrichtigung bei neuen Preisempfehlungen aus dem Revenue
  Management.
- Hinweise bei neuen Buchungen oder Stornierungen.
- Versand der fertigen Monatsauswertung in einen Kanal.

Technisch funktioniert das über sogenannte **Incoming Webhooks**: Slack stellt
eine URL bereit, an die ein Python-Skript per HTTP-Request eine Nachricht
schickt.

### Mini-Beispiel (Python)

```python
import requests

# Webhook-URL aus den Slack-App-Einstellungen (niemals committen!)
WEBHOOK_URL = "https://hooks.slack.com/services/XXX/YYY/ZZZ"

def sende_slack_nachricht(text: str) -> None:
    """Sendet eine einfache Textnachricht an einen Slack-Kanal."""
    requests.post(WEBHOOK_URL, json={"text": text})

sende_slack_nachricht("Neue Preisempfehlung: Doppelzimmer +12 € für nächstes Wochenende.")
```

> **Hinweis:** Die Webhook-URL ist ein Geheimnis und gehört nicht ins
> Repository, sondern in eine `.env`-Datei oder die Umgebungsvariablen (siehe
> Konvention „Sensible Daten" in der `CLAUDE.md`).
