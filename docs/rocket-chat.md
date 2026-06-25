# Rocket.Chat – Funktionen und Kosten

Rocket.Chat ist eine selbst-hostbare, quelloffene Kommunikationsplattform –
mehr als ein reiner Team-Chat. Sie eignet sich für die interne Kommunikation
**und** für die Gästekommunikation (Live-Chat, WhatsApp etc.). Da im Hotel
Aquarius bereits ein **VPS** vorhanden ist, kann Rocket.Chat kostenlos selbst
betrieben werden – die Daten bleiben dabei vollständig im eigenen Haus
(DSGVO-freundlich).

> Stand der Preisangaben: 2026. Preise und Limits ändern sich – vor einer
> Entscheidung auf <https://www.rocket.chat/pricing> bzw. beim Vertrieb prüfen.

## Funktionen

### 1. Team-Chat (die Slack-Basis)

- **Kanäle (Channels)** – öffentlich oder privat, z. B. `#rezeption`,
  `#restaurant`, `#technik`
- **Direktnachrichten** – 1:1 und Gruppen
- **Threads** – gebündelte Antworten an einer Nachricht
- **Diskussionen (Discussions)** – eigener Unterraum aus einer Nachricht heraus
- **Teams** – Bündel mehrerer Kanäle für eine Abteilung
- **Erwähnungen** (`@name`, `@all`, `@here`), Emoji-Reaktionen, Anpinnen,
  Markieren, Zitieren, Bearbeiten, Löschen
- **Volltextsuche** über alle Nachrichten und Dateien
- **Sprachnachrichten** und Datei-Uploads (Bilder, PDFs, Excel …)

### 2. Audio & Video

- **Sprach- und Videoanrufe** (1:1 und Gruppen)
- **Videokonferenzen** über Integrationen: **Jitsi** (kostenlos, selbst
  hostbar), BigBlueButton oder Google Meet
- **Bildschirmfreigabe**

### 3. Omnichannel / Live-Chat (Highlight für das Hotel)

Bündelt die **Gästekommunikation** an einem Ort:

- **Live-Chat-Widget** für die Hotel-Website – Gästeanfragen landen direkt bei
  der Rezeption in Rocket.Chat
- Eingehende Nachrichten aus mehreren Kanälen gebündelt: **WhatsApp Business**,
  **Facebook Messenger / Instagram**, **E-Mail**, **SMS / Telegram**
- **Warteschlangen & Zuweisung** von Anfragen an Mitarbeiter
- Vorgefertigte **Standardantworten** (Canned Responses)

### 4. Automatisierung & Integrationen

- **Incoming/Outgoing Webhooks** – ideal für die Python-Module des Projekts
  (Buchungsbenachrichtigungen, Preisempfehlungen, Monatsauswertung automatisch
  in einen Kanal posten)
- **REST-API** und Realtime-API – vollständige Steuerung von außen
- **Bots & Chatbots** – auch Anbindung an KI/LLM möglich (z. B. Gäste-FAQ)
- **Slash-Commands** (eigene `/befehle`)
- **App-Marketplace** (Jira, GitHub, Google Drive, Zapier …)

### 5. Sicherheit & Datenschutz

- **Selbst-Hosting** auf dem eigenen VPS – Daten bleiben im Haus
- **Ende-zu-Ende-Verschlüsselung (E2EE)** für sensible Kanäle
- **Zwei-Faktor-Authentifizierung (2FA)**
- **LDAP / SSO / OAuth** (Login z. B. über Google/Microsoft)
- **Rollen & Berechtigungen** fein einstellbar (Admin, Moderator, Nutzer, Gast)
- **Audit-Logs**

### 6. Plattformen

- **Web-Browser**, **Desktop-Apps** (Windows/Mac/Linux), **Mobile-Apps**
  (iOS/Android)
- Eigene gebrandete App in höheren Editionen möglich

### 7. Sonstiges

- **Mehrsprachig** (deutsche Oberfläche vorhanden)
- **Gäste-Zugänge** (externe Personen in einzelne Kanäle einladen)
- **Anpassbares Design** (eigenes Logo, Farben)
- **Echtzeit-Übersetzung** von Nachrichten

## Kosten

Der **interne Team-Chat** (Mitarbeiter untereinander) ist im self-hosted
Betrieb kostenlos. Kosten entstehen vor allem beim **Omnichannel** – und zwar
nicht pro Nutzer, sondern über **MAC (Monthly Active Contacts)**.

### Was ist ein MAC?

Ein **MAC** ist ein **externer Kontakt** (ein Gast/Kunde, kein Mitarbeiter),
der in einem Monat mindestens **eine Konversation** über einen
Omnichannel-Weg startet (Website-Live-Chat, WhatsApp, E-Mail, SMS).

- Zählt **pro Person und Monat**, unabhängig von der Anzahl der Nachrichten.
- Zählt nur bei aktiver Kontaktaufnahme durch den Gast.
- Der Zähler wird **jeden Kalendermonat zurückgesetzt**.

> Beispiel: 80 verschiedene Gäste schreiben in einem Monat über den
> Website-Chat → 80 MACs.

### Plan-Übersicht (Stand 2026)

| Plan | Omnichannel / MACs | Kosten |
|------|--------------------|--------|
| **Starter** (self-hosted) | **100 MACs/Monat inklusive** | **kostenlos** (bis ~25–50 Nutzer) |
| **Community** (Open Source) | nur Kern-Messaging, Omnichannel stark eingeschränkt | kostenlos |
| **Enterprise** (self-hosted) | individuell skalierbar via MAC-Packs | Angebot über Vertrieb |

- **MAC-Packs:** Bei Bedarf zusätzliche Pakete zu je **bis zu 3.000 Kontakten/
  Monat**; Preis nur auf Anfrage (Enterprise).
- Der frühere **Pro-Plan wurde am 29.04.2026 eingestellt**; einen festen
  öffentlichen Pro-Nutzer-Preis für Omnichannel gibt es nicht mehr.

### Bedeutung für Hotel Aquarius

- Die **100 kostenlosen MACs/Monat** reichen für den Einstieg oft aus
  (= 100 verschiedene anfragende Gäste pro Monat).
- **Saison beachten:** In der Hochsaison (Sommer) kann die Zahl anfragender
  Gäste schnell über 100 steigen → dann wird Omnichannel kostenpflichtig
  (Enterprise-Angebot einholen).
- Der reine interne Team-Chat bleibt dauerhaft kostenlos – MACs zählen
  **ausschließlich externe Gäste** im Omnichannel.

## Rocket.Chat vs. Mattermost (kurz)

| | Rocket.Chat | Mattermost |
|---|-------------|------------|
| Team-Chat | ✅ | ✅ (schlanker, „Slack-näher") |
| Live-Chat für Website / WhatsApp | ✅ stark | ❌ kaum |
| Funktionsumfang | sehr groß | fokussierter |
| Ressourcenbedarf (VPS) | etwas höher | etwas geringer |
| Ideal wenn … | **Gästekommunikation** (Website-Chat) mit reinholen | nur **internes Team** |

**Fazit:** Für reine interne Schichtkommunikation genügt Mattermost. Sollen
**Website-Live-Chat und WhatsApp-Gästeanfragen** mitgebündelt werden, ist
**Rocket.Chat** die bessere Wahl – alles in einem Tool.

## Quellen

- Rocket.Chat – Monthly Active Contacts (MACs):
  <https://docs.rocket.chat/docs/monthly-active-contacts-macs>
- Rocket.Chat – Our Plans: <https://docs.rocket.chat/docs/our-plans>
- Rocket.Chat – Omnichannel FAQ: <https://docs.rocket.chat/docs/omnichannel-faqs>
- Rocket.Chat – Pricing: <https://www.rocket.chat/pricing>
- Rocket.Chat – New Starter & Pro plans:
  <https://www.rocket.chat/blog/new-starter-pro-plans>
