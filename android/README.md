# Voice Claude – Android-App

Sprachgesteuerte Claude-App für das **Samsung Galaxy S23** (und andere Android-13+-Geräte).

## Funktion

1. **Beim Start** wird automatisch das Mikrofon aktiviert und gelauscht.
2. Das Gesprochene wird per Android-Spracherkennung in **Text** umgewandelt.
3. Der Text wird – je nach gewähltem **Modus** – als Prompt verarbeitet.
4. In den **Einstellungen** lassen sich Modus, Modell, Sprache und mehr wählen.

## Modi (in den Einstellungen wählbar)

| Modus | Verhalten |
|-------|-----------|
| **Neuer Chat (API)** | Prompt geht direkt an die Anthropic Messages API, die Antwort erscheint in der App. Das **Modell** ist wählbar (Opus 4.8 / Sonnet 4.6 / Haiku 4.5). |
| **Claude-Code-Sitzung** | Der erkannte Text wird in die Zwischenablage kopiert und die Claude-Code-Oberfläche geöffnet (Standard `claude.ai/code`, URL einstellbar). Dort einfügen. |
| **Cowork** | Wie oben, öffnet die Cowork-Oberfläche (Standard `claude.ai`, URL einstellbar). |

> Hinweis: Es gibt keine öffentliche Schnittstelle, um aus einer Fremd-App eine
> Claude-Code- oder Cowork-Sitzung mit vorbefülltem Prompt programmatisch zu
> starten. Daher der Zwischenablage-/Öffnen-Weg für diese beiden Modi. Nur der
> Modus „Neuer Chat" kommuniziert direkt per API.

## Einstellungen

- **Anthropic API-Key** – persönlicher Schlüssel (`sk-ant-…`), wird nur lokal im
  app-privaten Speicher abgelegt, nie committet.
- **Modus** – siehe Tabelle oben.
- **Modell** – verwendetes Claude-Modell (nur Modus „Neuer Chat").
- **Claude-Code-URL / Cowork-URL** – frei anpassbar.
- **Sprache der Spracherkennung** – Deutsch / English.
- **Mikrofon beim Start aktivieren** – an/aus.
- **Automatisch senden** – erkannten Text sofort abschicken.

## Build & Installation

Voraussetzungen: **Android Studio** (Giraffe oder neuer), JDK 17.

```bash
# Projekt in Android Studio öffnen:
#   File ▸ Open ▸ hotel-aquarius/android
# Android Studio richtet den Gradle-Wrapper automatisch ein.

# Galaxy S23 per USB verbinden, USB-Debugging aktivieren, dann "Run".

# Alternativ per CLI (nachdem der Wrapper erzeugt wurde):
./gradlew :app:installDebug
```

Beim ersten Start fragt die App die **Mikrofon-Berechtigung** an.

## Technik

- Kotlin, Min-SDK 26, Target-SDK 34
- `android.speech.SpeechRecognizer` für Sprache→Text
- OkHttp für die Anthropic Messages API (`anthropic-version: 2023-06-01`)
- AndroidX Preference für den Einstellungs-Screen

## Sicherheit

Der API-Key liegt ausschließlich im app-privaten Speicher des Geräts (Android-Sandbox)
und wird weder ins Repository geschrieben noch an Dritte übertragen – nur an
`api.anthropic.com`.
