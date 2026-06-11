#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tuya-/Smart-Life-Sensor-Anbindung – Hotel Aquarius
===================================================
Liest Temperatur- und Luftfeuchte-Werte von Tuya-/Smart-Life-WLAN-Sensoren
(z. B. Comboss TH02 Pro, baugleich Zecamin/Chatthen) aus der Tuya-Cloud und
speichert sie – 24/7 – in DERSELBEN SQLite-Datenbank wie die Govee-Sensoren
(``data/sensors.db``, Tabelle ``readings``, Spalte ``source='tuya'``).

Damit erscheinen die Tuya-Sensoren automatisch im bestehenden /sensoren-Dashboard.

Voraussetzung (einmalig durch den Nutzer)
-----------------------------------------
* Sensoren in der Smart-Life-/Tuya-Smart-App ans 2,4-GHz-WLAN bringen.
* Auf iot.tuya.com ein Cloud-Projekt anlegen (Data Center = Central Europe),
  Smart-Life-App-Account per QR-Code verknüpfen.
* Access ID + Access Secret + (mind. eine) device_id bereitstellen.

Umgebungsvariablen
------------------
TUYA_ACCESS_ID            Pflicht – Client-ID des Tuya-Cloud-Projekts.
TUYA_ACCESS_SECRET        Pflicht – Client-Secret.
TUYA_REGION               Data-Center-Region (Default "eu" = Central Europe).
TUYA_DEVICE_IDS           Optional – Komma-Liste der device_ids. Leer = automatisch
                          alle Klima-Sensoren des Projekts entdecken.
TUYA_POLL_INTERVAL_SEC    Abstand zwischen Messungen (Default 600 s = 10 min).
TUYA_TEMP_SCALE           Teiler für die Roh-Temperatur (Default 10 → 227 = 22,7 °C).

Achtung Trial-Falle
-------------------
Das Tuya "IoT Core / Cloud Development Plan" ist ein Trial und läuft ab; danach
schlagen alle API-Calls fehl (Fehler 28841002 "subscription expired"). Muss
regelmäßig kostenlos verlängert werden (Cloud > My Services > Extend Trial Period).
Ein solcher Ausfall wird im Status (last_error) sichtbar gemacht.
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from typing import Any, Optional

# Geteilte Speicher-/Zeitzonen-Schicht (Tabelle liegt in govee_sensors)
import govee_sensors as gs

try:
    import tinytuya  # noqa: F401
    TINYTUYA_OK = True
except ImportError:
    TINYTUYA_OK = False


# ── Konfiguration ───────────────────────────────────────────────────────────

ACCESS_ID = os.getenv("TUYA_ACCESS_ID", "").strip()
ACCESS_SECRET = os.getenv("TUYA_ACCESS_SECRET", "").strip()
REGION = os.getenv("TUYA_REGION", "eu").strip() or "eu"
DEVICE_IDS = [d.strip() for d in os.getenv("TUYA_DEVICE_IDS", "").split(",") if d.strip()]
POLL_INTERVAL_SEC = int(os.getenv("TUYA_POLL_INTERVAL_SEC", "600"))
TEMP_SCALE = float(os.getenv("TUYA_TEMP_SCALE", "10") or "10")
DEVICE_REFRESH_SEC = int(os.getenv("TUYA_DEVICE_REFRESH_SEC", "1800"))

# Tuya-DP-/Statuscodes (je nach Firmware unterschiedlich benannt)
TEMP_CODES = {"va_temperature", "temp_current", "temperature", "temp_current_external"}
HUM_CODES = {"va_humidity", "humidity_value", "humidity", "va_humidity_external"}
ONLINE_CODES = {"online"}
BATTERY_CODES = {"battery_percentage", "battery_value", "va_battery", "residual_electricity"}
# Geräte-Kategorien, die wir als Klima-Sensor behandeln
CLIMATE_CATEGORIES = {"wsdcg", "wnykq", "ldcg"}


def is_configured() -> bool:
    """True, wenn Tuya nutzbar ist (Bibliothek + Zugangsdaten vorhanden)."""
    return bool(TINYTUYA_OK and ACCESS_ID and ACCESS_SECRET)


def to_celsius(raw: Optional[float]) -> Optional[float]:
    """Rohwert nach Celsius. Tuya liefert i. d. R. ×10 (227 = 22,7 °C)."""
    if raw is None:
        return None
    scale = TEMP_SCALE if TEMP_SCALE else 1.0
    return round(raw / scale, 2)


def _num(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ── Tuya-Cloud-Client ─────────────────────────────────────────────────────────

class TuyaClient:
    """Dünner Wrapper um tinytuya.Cloud (synchron; im Poller via to_thread)."""

    def __init__(self, access_id: str, access_secret: str, region: str,
                 bootstrap_device_id: str = ""):
        if not TINYTUYA_OK:
            raise RuntimeError("tinytuya nicht installiert (pip install tinytuya)")
        self._cloud = tinytuya.Cloud(
            apiRegion=region,
            apiKey=access_id,
            apiSecret=access_secret,
            apiDeviceID=bootstrap_device_id or "",
        )

    @staticmethod
    def _check(resp: Any) -> Any:
        """Tuya-Fehler (z. B. abgelaufenes Trial) als Exception werfen."""
        if isinstance(resp, dict) and resp.get("success") is False:
            raise RuntimeError(
                f"Tuya API Fehler {resp.get('code')}: {resp.get('msg')}"
            )
        return resp

    def list_devices(self) -> list[dict]:
        resp = self._cloud.getdevices(verbose=False) if hasattr(self._cloud, "getdevices") else []
        if isinstance(resp, dict):
            self._check(resp)
            return resp.get("result", resp.get("devices", [])) or []
        return resp or []

    def get_status(self, device_id: str) -> list[dict]:
        resp = self._cloud.getstatus(device_id)
        self._check(resp)
        if isinstance(resp, dict):
            return resp.get("result", []) or []
        return resp or []


# ── Parsing ────────────────────────────────────────────────────────────────

def extract_values(status: list[dict]) -> dict:
    """Aus dem Tuya-status-Array (code/value-Paare) Temp/Feuchte/Online ziehen."""
    temp_raw: Optional[float] = None
    humidity: Optional[float] = None
    online: Optional[bool] = None
    battery: Optional[float] = None
    for item in status or []:
        code = item.get("code")
        value = item.get("value")
        if code in TEMP_CODES:
            temp_raw = _num(value)
        elif code in HUM_CODES:
            humidity = _num(value)
        elif code in BATTERY_CODES:
            battery = _num(value)
        elif code in ONLINE_CODES:
            online = bool(value)
    return {
        "temp_raw": temp_raw,
        "temp_c": to_celsius(temp_raw),
        "humidity": humidity,
        "battery": battery,
        "online": online,
    }


def is_climate_device(dev: dict) -> bool:
    """Ist das Gerät ein Temperatur-/Feuchte-Sensor?"""
    cat = (dev.get("category") or "").lower()
    if cat in CLIMATE_CATEGORIES:
        return True
    name = (dev.get("product_name") or dev.get("name") or "").lower()
    return any(k in name for k in ("thermo", "hygro", "temp", "humid", "klima"))


# ── Poller (Hintergrund-Task, 24/7) ────────────────────────────────────────────

class TuyaPoller:
    """Fragt die Tuya-Cloud 24/7 zyklisch ab und speichert die Werte."""

    def __init__(self):
        self.client: Optional[TuyaClient] = None
        self.last_poll_utc: Optional[str] = None
        self.last_result: str = "noch nicht gelaufen"
        self.last_error: Optional[str] = None
        self.last_device_count: int = 0
        self._name_map: dict = {}
        self._targets_cache: Optional[list] = None
        self._cached_at: float = 0.0
        self._task: Optional[asyncio.Task] = None
        self._stop = asyncio.Event()

    def status(self) -> dict:
        return {
            "configured": is_configured(),
            "tinytuya_installed": TINYTUYA_OK,
            "running": self._task is not None and not self._task.done(),
            "region": REGION,
            "device_ids_configured": len(DEVICE_IDS),
            "poll_interval_sec": POLL_INTERVAL_SEC,
            "temp_scale": TEMP_SCALE,
            "last_poll_utc": self.last_poll_utc,
            "last_result": self.last_result,
            "last_error": self.last_error,
            "last_device_count": self.last_device_count,
        }

    def _ensure_client(self) -> TuyaClient:
        if self.client is None:
            self.client = TuyaClient(
                ACCESS_ID, ACCESS_SECRET, REGION,
                bootstrap_device_id=DEVICE_IDS[0] if DEVICE_IDS else "",
            )
        return self.client

    def _resolve_targets(self) -> list[str]:
        """Liefert die zu pollenden device_ids und füllt die Namens-Map.
        Nutzt die explizite Liste (falls gesetzt) + getdevices() für Namen."""
        import time
        now = time.monotonic()
        if self._targets_cache is not None and now - self._cached_at <= DEVICE_REFRESH_SEC:
            return self._targets_cache

        client = self._ensure_client()
        devices = []
        try:
            devices = client.list_devices()
        except Exception as e:
            print(f"[tuya] Geräteliste-Fehler: {e}")

        for d in devices:
            did = d.get("id") or d.get("device_id")
            if did:
                self._name_map[did] = d.get("name") or d.get("product_name") or did

        # Automatisch entdeckte Klima-Sensoren …
        discovered = [
            (d.get("id") or d.get("device_id"))
            for d in devices if is_climate_device(d)
        ]
        # … vereint mit den explizit gesetzten IDs (eine genügt als "Einstieg"
        # für die Geräteliste). Reihenfolge erhalten, Duplikate raus.
        seen: set = set()
        targets: list[str] = []
        for t in list(DEVICE_IDS) + discovered:
            if t and t not in seen:
                seen.add(t)
                targets.append(t)

        self._targets_cache = targets
        self._cached_at = now
        return targets

    async def poll_once(self) -> int:
        if not is_configured():
            return 0
        tz = gs._tz()
        now = datetime.now(tz)
        now_utc = datetime.now(timezone.utc)
        ts_utc = now_utc.isoformat(timespec="seconds")
        ts_local = now.isoformat(timespec="seconds")
        day = now.strftime("%Y-%m-%d")

        targets = await asyncio.to_thread(self._resolve_targets)
        self.last_device_count = len(targets)

        stored = 0
        for device_id in targets:
            try:
                status = await asyncio.to_thread(self._ensure_client().get_status, device_id)
                vals = extract_values(status)
            except Exception as e:
                # Trial-Ablauf o. Ä.: sichtbar machen, aber nicht crashen
                self.last_error = str(e)
                print(f"[tuya] Status-Fehler {device_id}: {e}")
                continue
            if vals["temp_raw"] is None and vals["humidity"] is None:
                continue
            name = self._name_map.get(device_id, device_id)
            await asyncio.to_thread(
                gs.insert_reading,
                ts_utc=ts_utc, ts_local=ts_local, day=day,
                device=device_id, sku="TH02 Pro", name=name,
                temp_c=vals["temp_c"], temp_raw=vals["temp_raw"],
                humidity=vals["humidity"], online=vals["online"],
                source="tuya", battery=vals.get("battery"),
            )
            stored += 1
        self.last_poll_utc = ts_utc
        return stored

    async def _run(self) -> None:
        await asyncio.to_thread(gs.init_db)
        print(f"[tuya] Poller gestartet · 24/7-Aufzeichnung · "
              f"Region {REGION} · Intervall {POLL_INTERVAL_SEC}s")
        while not self._stop.is_set():
            now = datetime.now(gs._tz())
            try:
                n = await self.poll_once()
                self.last_result = f"ok – {n} Sensor(en) gespeichert"
                if n > 0:
                    self.last_error = None
                print(f"[tuya] {now:%Y-%m-%d %H:%M:%S} – {n} Sensor(en) gespeichert")
            except Exception as e:
                self.last_result = "Fehler"
                self.last_error = str(e)
                print(f"[tuya] Poll-Fehler: {e}")
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=POLL_INTERVAL_SEC)
            except asyncio.TimeoutError:
                pass

    def start(self) -> None:
        if not is_configured():
            why = "tinytuya fehlt" if not TINYTUYA_OK else "TUYA_ACCESS_ID/SECRET fehlt"
            print(f"[tuya] Poller deaktiviert ({why}).")
            return
        self._stop.clear()
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                self._task.cancel()
