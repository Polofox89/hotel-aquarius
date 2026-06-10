#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Govee-Verbindungstest – Hotel Aquarius
=======================================
Prüft mit deinem API-Key, welche Govee-Geräte über die Cloud-API sichtbar sind
und welche Temperatur-/Feuchte-Werte sie aktuell liefern.

Damit klären wir VOR dem Dauerbetrieb, ob der Smart Thermometer R1 (H5108)
über das H5151-Gateway in der Entwickler-API erscheint.

Aufruf (PowerShell, Key wird NICHT gespeichert):
    python govee_probe.py DEIN_API_KEY
oder mit Umgebungsvariable:
    $env:GOVEE_API_KEY="DEIN_API_KEY"; python govee_probe.py

Der Key wird nur für diesen einen Aufruf verwendet und nirgends abgelegt.
"""

from __future__ import annotations

import json
import sys
import uuid
import os

# Windows-Konsole auf UTF-8 stellen (sonst Absturz bei Emoji/Pfeilen unter cp1252)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    import httpx
except ImportError:
    sys.exit("Bitte zuerst:  pip install httpx")

BASE = "https://openapi.api.govee.com"
DEVICES_URL = f"{BASE}/router/api/v1/user/devices"
STATE_URL = f"{BASE}/router/api/v1/device/state"

TEMP_INSTANCES = {"sensorTemperature", "temperature"}
HUM_INSTANCES = {"sensorHumidity", "humidity"}


def mask(device_id: str) -> str:
    """Geräte-MAC für die Ausgabe teilweise maskieren."""
    if len(device_id) <= 6:
        return device_id
    return device_id[:3] + "…" + device_id[-3:]


def main() -> None:
    key = (sys.argv[1] if len(sys.argv) > 1 else os.getenv("GOVEE_API_KEY", "")).strip()
    if not key:
        sys.exit("Kein API-Key. Aufruf:  python govee_probe.py DEIN_API_KEY")

    headers = {"Govee-API-Key": key, "Content-Type": "application/json"}

    print("→ Frage Geräteliste ab …\n")
    with httpx.Client(timeout=20.0) as client:
        r = client.get(DEVICES_URL, headers=headers)
        if r.status_code == 401:
            sys.exit("✗ 401 Unauthorized – API-Key ungültig.")
        r.raise_for_status()
        devices = r.json().get("data", []) or []

        if not devices:
            print("✗ Keine Geräte sichtbar. Prüfe: Ist das H5151-Gateway in der")
            print("  Govee-Home-App online und sind die Sensoren ihm zugeordnet?")
            return

        print(f"✓ {len(devices)} Gerät(e) sichtbar:\n")
        climate_found = False
        for d in devices:
            sku = d.get("sku", "")
            dev_id = d.get("device", "")
            name = d.get("deviceName") or sku
            dtype = d.get("type", "")
            instances = [c.get("instance") for c in d.get("capabilities", []) or []]
            is_climate = bool(
                (TEMP_INSTANCES | HUM_INSTANCES) & set(instances)
            ) or "thermometer" in dtype.lower() or "hygrometer" in dtype.lower()

            flag = "🌡️ KLIMA-SENSOR" if is_climate else "  (anderes Gerät)"
            print(f"  {flag}  {name}  [{sku}]  {mask(dev_id)}")
            print(f"      type={dtype}")
            print(f"      capabilities={instances}")

            if is_climate:
                climate_found = True
                # Aktuellen Zustand abfragen
                body = {"requestId": str(uuid.uuid4()),
                        "payload": {"sku": sku, "device": dev_id}}
                sr = client.post(STATE_URL, headers=headers, json=body)
                if sr.status_code == 200:
                    payload = sr.json().get("payload", {})
                    temp = hum = None
                    for c in payload.get("capabilities", []) or []:
                        inst = c.get("instance")
                        val = (c.get("state") or {}).get("value")
                        if inst in TEMP_INSTANCES:
                            temp = val
                        elif inst in HUM_INSTANCES:
                            hum = val
                    print(f"      → Temperatur (roh): {temp}   Feuchte: {hum} %")
                    if temp is not None:
                        try:
                            t = float(temp)
                            celsius = (t - 32) * 5 / 9 if t > 45 else t
                            note = "(als °F interpretiert)" if t > 45 else "(als °C interpretiert)"
                            print(f"      → ≈ {celsius:.1f} °C  {note}")
                        except (TypeError, ValueError):
                            pass
                else:
                    print(f"      → Status-Abfrage fehlgeschlagen: HTTP {sr.status_code}")
            print()

        print("─" * 60)
        if climate_found:
            print("✓ ERGEBNIS: Klima-Sensor(en) sind über die Cloud-API erreichbar.")
            print("  Das Dashboard kann diese Werte automatisch aufzeichnen. 🎉")
        else:
            print("✗ ERGEBNIS: Es sind Geräte sichtbar, aber KEIN Klima-Sensor.")
            print("  Der H5108 erscheint dann nicht in der Entwickler-API – wir")
            print("  bräuchten die lokale BLE-Bridge-Variante. Schick mir die")
            print("  obige Ausgabe, dann plane ich den nächsten Schritt.")


if __name__ == "__main__":
    main()
