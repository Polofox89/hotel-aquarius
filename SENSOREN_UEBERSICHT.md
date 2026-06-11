# Sensor-Dashboard Hotel Aquarius – Gesamtüberblick

Stand: 2026-06-11. Kurz-Referenz für eine neue Session zum Thema „Sensoren".

---

## Was es ist
Ein **Temperatur-/Feuchte-Monitoring** als Teil der bestehenden FastAPI-Web-App.
Liest Sensoren **rund um die Uhr (24/7)** aus zwei Hersteller-Clouds, speichert alles in
**SQLite** und zeigt es grafisch (Chart.js) auf einer Seite.

- **Aufruf:** <https://buffet.hotel-aquarius.com/sensoren> (hinter dem **Admin-Basic-Auth**, wie das Tagesbuffet-Admin)
- **Zweck:** Raumklima- und **Kühlketten-/HACCP-Kontrolle** am Frühstücksbuffet.

## Eingebundene Sensoren

| Sensor (Name in App) | Marke / Modell | Anbindung | Werte |
|---|---|---|---|
| Kühlschrank | Govee H5108 | H5151-WLAN-Gateway → Govee-Cloud | Temp |
| Fruchtcocktail | Govee H5108 | H5151-Gateway → Govee-Cloud | Temp |
| Wurstplatte | Govee H5108 | H5151-Gateway → Govee-Cloud | Temp |
| Getränke Kühlschrank | Comboss **TH02 Pro** (Tuya/Smart Life) | Tuya-Cloud (tinytuya) | Temp + **Feuchte** + **Akku** |

- **Govee H5108** ist **BLE-only** → braucht das **H5151-Gateway**; liefert über die Cloud **nur Temperatur** (keine Feuchte/Akku). API liefert °F → intern ÷ nach °C.
- **Comboss TH02 Pro** = White-Label-**Tuya**-Gerät (auch Zecamin/Chatthen). Direkt im 2,4-GHz-WLAN, **kein Gateway**. Liefert Temp (`va_temperature`÷10), Feuchte (`va_humidity`), Akku (`battery_percentage`).
- **3 weitere Comboss** erscheinen **automatisch**, sobald online (App-Account ist per „Automatic Link" verknüpft).

## Dashboard-Funktionen
- **Live-Kacheln**: Temp, Feuchte (falls vorhanden), **Akku** (rot bei ≤ 20 %, nur Tuya).
- **Zwei umschaltbare Ansichten** (immer nur eine aktiv):
  - **24 Stunden** (0–24 Uhr) → Überschrift „Tages-Zusammenfassung".
  - **Kontrolle 7–10 Uhr** → Überschrift **„Frühstückszeit"**; Min/Max/Ø nur für diese 3 Stunden.
- **Diagramme** (Temp + Feuchte) je Sensor; **rote Grenzlinie bei 7 °C** im Temp-Chart.
- **Legenden-Filter** (Sensor an-/ausklicken) bleibt beim Auto-Refresh & Moduswechsel erhalten; **Button „Alle anzeigen"** setzt ihn zurück.
- Datums-Navigation (frühere Tage), Auto-Refresh alle 60 s.

## Technik / Code (Repo)
- **Repo:** github.com/Polofox89/hotel-aquarius · Branch **main**
- **Backend:** FastAPI (`web_app.py`), uvicorn `127.0.0.1:8000`, zwei Hintergrund-Poller.
  - `govee_sensors.py` – Govee-Client + Poller **+ gemeinsame SQLite-Schicht** (Tabelle `readings`).
  - `tuya_sensors.py` – Tuya-Client (`tinytuya` Cloud-Modus) + Poller; schreibt in dieselbe Tabelle, markiert mit `source='tuya'`.
  - `govee_probe.py` – Verbindungstest Govee (Standalone).
- **Frontend:** `static/sensoren.html` + `static/sensoren.js` (+ gemeinsame `static/style.css`).
- **DB:** `data/sensors.db` (SQLite, in `.gitignore`). Tabelle `readings` mit u. a. `source` (govee/tuya) und `battery`.
- **Intervalle:** Govee alle 120 s, Tuya alle 600 s (24/7).

## Deployment (VPS)
- **SSH:** `ssh buffet` (root@31.70.81.178, Ubuntu) · App in **`/opt/tagesbuffet`** (Git-Checkout von origin/main, venv `.venv`).
- **Dienst:** systemd **`tagesbuffet.service`** (uvicorn). nginx-Site **`buffet`** (Reverse-Proxy + Basic-Auth, Let's-Encrypt).
- **Ablauf:** lokal committen → `git push origin main` → auf VPS `cd /opt/tagesbuffet && git pull`.
  - **Neustart nötig** (`systemctl restart tagesbuffet`) nur bei **Python**-Änderungen. Reine **HTML/JS/CSS**-Änderungen brauchen keinen Neustart (Cache-Busting per Datei-mtime).

## Konfiguration (`/etc/tagesbuffet.env`, NICHT in Git, mode 600)
```
GOVEE_API_KEY=…
TUYA_ACCESS_ID=…            # Tuya-Cloud-Projekt „Hotel Aquarius Sensoren"
TUYA_ACCESS_SECRET=…        # (Project Code p1781190317951qkvvyv, Central Europe)
TUYA_REGION=eu
TUYA_DEVICE_IDS=…           # mind. eine device_id als „Einstieg"; Rest wird auto-erkannt
```
Weitere optionale Variablen (Default in Klammern): `GOVEE_POLL_INTERVAL_SEC` (120),
`GOVEE_WINDOW_START/END` (07:00/10:00, nur Anzeige-Fenster), `GOVEE_TEMP_INPUT_UNIT` (f),
`TUYA_POLL_INTERVAL_SEC` (600), `TUYA_TEMP_SCALE` (10). Details: `README_Sensoren.md`.

## API-Endpunkte (alle hinter Basic-Auth)
`/sensoren` (Seite) · `/api/sensors/status` · `/api/sensors/latest` ·
`/api/sensors/history?day=YYYY-MM-DD` · `/api/sensors/days` · `/api/sensors/probe` (Govee live) ·
`/api/sensors/tuya/status` · `/api/sensors/tuya/probe` (Tuya live).

## Wichtige Hinweise / offene Punkte
- ⚠️ **Tuya-Trial-Falle:** Der kostenlose Tuya-„IoT Core"-Plan läuft nach Monaten ab; dann
  stoppt **nur** die Comboss-Aufzeichnung (Govee läuft weiter). Verlängern unter
  **Cloud → My Services → „Extend Trial Period"** (kostenlos). Ein Ausfall wird im Dashboard
  als Fehler (`last_error`) sichtbar. *(Knopf erscheint erst, wenn der Ablauf näher rückt.)*
- 🔋 **„Getränke Kühlschrank"**: Akku zuletzt ~14 % → AAA bald wechseln.
- ➕ Weitere Comboss-Sensoren einfach in der Smart-Life-App einrichten → erscheinen automatisch.

## Setup-Schritte, die einmalig gemacht wurden (zur Referenz)
1. Govee: API-Key + H5151-Gateway (Sensoren in Govee-App benannt).
2. Tuya: Konto auf iot.tuya.com, Cloud-Projekt (Smart Home, **Central Europe**),
   API-Dienste „Authorize", **„Link App Account" → „Tuya App Account Authorization" → Automatic Link** (QR mit Smart-Life-App gescannt). Access ID/Secret in die Env-Datei.
