# Govee-Sensor-Dashboard – Hotel Aquarius

Live-Anzeige + tägliche Aufzeichnung der Govee-Temperatur-/Feuchte-Sensoren
(Smart Thermometer R1 / **H5108** über das WLAN-Gateway **H5151**).

* **Aufzeichnung nur 07:00–10:00 Uhr** (Europe/Berlin)
* **Alle Tageswerte** landen in `data/sensors.db` (SQLite)
* Dashboard unter **`/sensoren`**, grafisch aufbereitet (Chart.js)

---

## ⚠️ Wichtig: H5108 braucht das H5151-Gateway

Der H5108 ist ein **reines Bluetooth-Gerät** und erscheint allein **nicht** in der
Govee-Cloud-API. Erst über das **WLAN-Gateway H5151** gelangen seine Werte in die
Cloud und damit zum VPS. Das Gateway muss also im Hotel-WLAN online sein.

---

## 1. Verbindung testen (vor dem Dauerbetrieb)

Prüft, ob deine Sensoren über die Cloud-API sichtbar sind. Der Key wird **nicht**
gespeichert:

```powershell
pip install httpx
python govee_probe.py DEIN_GOVEE_API_KEY
```

Erscheint ein „🌡️ KLIMA-SENSOR" mit aktuellem Temperatur-/Feuchtewert → alles gut.
Erscheint kein Klima-Sensor → die lokale BLE-Bridge-Variante ist nötig (melden).

Wenn die App schon läuft, geht der Test auch im Browser:
`https://hotel-aquarius.com/api/sensors/probe`

---

## 2. Lokal starten

```powershell
pip install -r requirements.txt
$env:GOVEE_API_KEY="DEIN_GOVEE_API_KEY"
uvicorn web_app:app --reload --port 8000
```

Dann öffnen: <http://localhost:8000/sensoren>

---

## 3. Auf dem VPS (systemd)

Der vorhandene Dienst `tagesbuffet.service` muss nur den API-Key als
Umgebungsvariable bekommen. In der Service-Datei
(`/etc/systemd/system/tagesbuffet.service`) ergänzen:

```ini
[Service]
Environment="GOVEE_API_KEY=DEIN_GOVEE_API_KEY"
Environment="BUFFET_DATA=/pfad/zu/data"
# optional:
# Environment="GOVEE_POLL_INTERVAL_SEC=120"
# Environment="GOVEE_TEMP_INPUT_UNIT=auto"
```

Danach:

```bash
pip install -r requirements.txt          # httpx + tzdata neu
sudo systemctl daemon-reload
sudo systemctl restart tagesbuffet
```

Die SQLite-Datenbank wird automatisch unter `$BUFFET_DATA/sensors.db` angelegt.
Sie liegt im Daten-Ordner (nicht in Git) und überlebt Deploys.

---

## Konfiguration (Umgebungsvariablen)

| Variable | Default | Zweck |
|----------|---------|-------|
| `GOVEE_API_KEY` | – | **Pflicht.** Ohne Key bleibt der Poller aus. |
| `GOVEE_WINDOW_START` | `07:00` | Beginn der Aufzeichnung |
| `GOVEE_WINDOW_END` | `10:00` | Ende der Aufzeichnung |
| `GOVEE_POLL_INTERVAL_SEC` | `120` | Abstand zwischen Messungen |
| `GOVEE_TZ` | `Europe/Berlin` | Zeitzone fürs Fenster |
| `GOVEE_TEMP_INPUT_UNIT` | `F` | `F`/`C`/`auto` – Einheit der API-Werte |
| `SENSORS_DB` | `$BUFFET_DATA/sensors.db` | Pfad zur Datenbank |

**Temperatur-Einheit:** Die Govee-API liefert für die Smart Thermometer R1 die
Temperatur in **Fahrenheit** (am Hotel-Account bestätigt) – deshalb ist `F` der
Standard, der intern nach °C umgerechnet wird. Sollte ein Account °C liefern,
`GOVEE_TEMP_INPUT_UNIT=C` setzen. (`auto` = Werte > 45 gelten als °F – nur als
Notlösung, scheitert bei Kühl-/Gefriersensoren wie dem Kühlhaus bei −1 °C.)

**Nur Temperatur, keine Feuchte:** Der Smart Thermometer R1 (H5108) liefert über
die Cloud nur `sensorTemperature`. Das Dashboard blendet die Luftfeuchte-Anzeige
automatisch aus, solange kein Sensor Feuchtewerte liefert.

**Sensoren benennen:** Unbenannt heißen in der API alle gleich („Smart Thermometer
R1"). Für sprechende Namen im Dashboard (z. B. „Kühlhaus", „Frühstücksraum") die
Sensoren in der **Govee-Home-App** umbenennen – das Dashboard übernimmt den Namen.

---

## API-Endpunkte

| Endpunkt | Zweck |
|----------|-------|
| `GET /sensoren` | Dashboard-Seite |
| `GET /api/sensors/status` | Poller-Status + Konfiguration |
| `GET /api/sensors/latest` | Neuester Wert je Sensor |
| `GET /api/sensors/history?day=YYYY-MM-DD` | Tageswerte + Zusammenfassung |
| `GET /api/sensors/days` | Tage mit Daten |
| `GET /api/sensors/devices` | Bekannte Sensoren |
| `GET /api/sensors/probe` | Live-Test gegen die Govee-API |
