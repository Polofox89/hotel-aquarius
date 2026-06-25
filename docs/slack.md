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

## Auf welchem Server läuft Slack?

Slack wird **nicht selbst gehostet**. Es ist ein Cloud-Dienst (Software as a
Service), den die Firma Slack Technologies (seit 2021 Teil von **Salesforce**)
selbst betreibt.

| Aspekt | Erklärung |
|--------|-----------|
| **Betreiber** | Slack Technologies / Salesforce |
| **Infrastruktur** | Cloud, überwiegend auf **Amazon Web Services (AWS)** |
| **Rechenzentren** | Weltweit verteilt; für EU-Kunden ist Datenspeicherung in der EU möglich |
| **Eigene Server** | Nicht nötig – nur App oder Browser erforderlich |

Der umgangssprachliche Begriff „Server" (wie bei Discord) entspricht in Slack
dem **Workspace** – das ist nur die logische Team-Umgebung (z. B. „Hotel
Aquarius"), kein physischer Rechner, den man selbst betreibt.

**Wichtig (Datenschutz):** Die Daten liegen in der Slack-Cloud, nicht im Haus.
Sensible Gästedaten daher nur mit Bedacht teilen.

**Self-Hosted-Alternative:** Wer Daten zwingend auf einem eigenen Server halten
will, kann **Mattermost** oder **Rocket.Chat** nutzen – für ein 54-Zimmer-Hotel
aber meist überdimensioniert.

## Kosten

Slack rechnet **pro aktivem Nutzer und Monat** ab. Preise Stand Anfang 2026
(können sich ändern – vor Abschluss auf slack.com prüfen; netto, zzgl. MwSt.):

| Tarif | Preis (ca.) | Enthalten |
|-------|-------------|-----------|
| **Free** | **0 €** | Nachrichtenverlauf der letzten 90 Tage, 1:1-Huddles, begrenzte Integrationen |
| **Pro** | **~7–9 € / Nutzer / Monat** (jährlich) | Voller Verlauf, Gruppen-Huddles, unbegrenzte Apps/Integrationen, Gäste-Zugänge |
| **Business+** | **~12–15 € / Nutzer / Monat** | Zusätzlich erweiterte Sicherheit, SSO, Compliance |
| **Enterprise Grid** | **individuell** | Große Konzerne – für ein Hotel irrelevant |

### Beispielrechnung Hotel Aquarius

```
 5 Nutzer × ~8 € × 12 Monate ≈ 480 € / Jahr  (zzgl. MwSt.)
10 Nutzer × ~8 € × 12 Monate ≈ 960 € / Jahr  (zzgl. MwSt.)
```

### Empfehlung

- **Mit dem Free-Tarif starten** – reicht für ein kleines Hotelteam oft völlig.
  Einziger Nachteil: Nachrichten älter als 90 Tage sind nicht durchsuchbar.
- **Upgrade auf Pro** erst, wenn voller Verlauf, Team-Video-Huddles oder viele
  Integrationen (z. B. Anbindung der Python-Module) gebraucht werden.
- Nur Mitarbeiter mit aktivem Zugang kosten Geld – inaktive Konten deaktivieren.
