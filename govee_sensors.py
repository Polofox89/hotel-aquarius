#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Govee-Sensor-Anbindung – Hotel Aquarius
========================================
Liest Temperatur- und Luftfeuchte-Werte der Govee-Sensoren (z. B. Smart
Thermometer R1 / H5108 über das WLAN-Gateway H5151) aus der Govee-Cloud-API
und speichert sie in einer SQLite-Datenbank.

Wichtige Eigenschaften
----------------------
* Aufzeichnung läuft 24/7 (rund um die Uhr). Das Fenster 07:00–10:00 Uhr
  (Europe/Berlin) dient nur der "Kontrolle"-Ansicht im Dashboard.
* Alle Messwerte werden tagesweise in ``data/sensors.db`` abgelegt.
* Robust: Fehler in einem Poll-Durchlauf legen die App nicht lahm.

Govee-API (v2)
--------------
Geräteliste:   GET  https://openapi.api.govee.com/router/api/v1/user/devices
Gerätestatus:  POST https://openapi.api.govee.com/router/api/v1/device/state
Header:        Govee-API-Key: <key>

Umgebungsvariablen
------------------
GOVEE_API_KEY            Pflicht – ohne Key ist der Poller deaktiviert.
GOVEE_POLL_INTERVAL_SEC  Abstand zwischen Messungen, 24/7 (Default 120).
GOVEE_DEVICE_REFRESH_SEC Geräteliste-Cache in Sekunden (Default 1800).
GOVEE_WINDOW_START       Beginn Kontroll-Ansicht "HH:MM" (Default "07:00", nur Anzeige).
GOVEE_WINDOW_END         Ende Kontroll-Ansicht  "HH:MM" (Default "10:00", nur Anzeige).
GOVEE_TZ                 Zeitzone (Default "Europe/Berlin").
GOVEE_TEMP_INPUT_UNIT    Einheit der API-Werte: "F" | "C" | "auto" (Default "F").
                         "auto": Werte > 45 werden als Fahrenheit interpretiert.
SENSORS_DB               Pfad zur SQLite-Datei (Default: $BUFFET_DATA/sensors.db).
"""

from __future__ import annotations

import asyncio
import os
import sqlite3
import time
import uuid
from datetime import datetime, time as time_cls, timezone
from pathlib import Path
from typing import Any, Optional

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover – Python < 3.9
    ZoneInfo = None  # type: ignore

import httpx


# ── Konfiguration ───────────────────────────────────────────────────────────

GOVEE_BASE = "https://openapi.api.govee.com"
DEVICES_URL = f"{GOVEE_BASE}/router/api/v1/user/devices"
STATE_URL = f"{GOVEE_BASE}/router/api/v1/device/state"

API_KEY = os.getenv("GOVEE_API_KEY", "").strip()
POLL_INTERVAL_SEC = int(os.getenv("GOVEE_POLL_INTERVAL_SEC", "120"))
# Geräteliste nur alle 30 min neu holen (schont die API im 24/7-Dauerbetrieb).
DEVICE_REFRESH_SEC = int(os.getenv("GOVEE_DEVICE_REFRESH_SEC", "1800"))
# Kontroll-Fenster: nur für die "Kontrolle 7-10 Uhr"-Ansicht – Aufzeichnung läuft 24/7.
WINDOW_START = os.getenv("GOVEE_WINDOW_START", "07:00")
WINDOW_END = os.getenv("GOVEE_WINDOW_END", "10:00")
TZ_NAME = os.getenv("GOVEE_TZ", "Europe/Berlin")
# Govee-v2-API liefert die Temperatur in Fahrenheit (bestätigt am Hotel-Account:
# Werte 72.68/74.12 = Raumtemperatur, 30.02 = Kühlhaus). Default daher "f".
TEMP_INPUT_UNIT = os.getenv("GOVEE_TEMP_INPUT_UNIT", "f").strip().lower()

_DATA_DIR = Path(os.getenv("BUFFET_DATA", str(Path(__file__).parent / "data")))
DB_PATH = Path(os.getenv("SENSORS_DB", str(_DATA_DIR / "sensors.db")))

# Govee-Capability-Instanzen für Temperatur / Feuchte
TEMP_INSTANCES = {"sensorTemperature", "temperature"}
HUM_INSTANCES = {"sensorHumidity", "humidity"}
ONLINE_INSTANCES = {"online"}


def _tz():
    """Zeitzonen-Objekt (Europe/Berlin) oder UTC als Fallback."""
    if ZoneInfo is not None:
        try:
            return ZoneInfo(TZ_NAME)
        except Exception:
            pass
    return timezone.utc


def _parse_hhmm(s: str, default: time_cls) -> time_cls:
    try:
        h, m = s.split(":")
        return time_cls(int(h), int(m))
    except Exception:
        return default


WINDOW_START_T = _parse_hhmm(WINDOW_START, time_cls(7, 0))
WINDOW_END_T = _parse_hhmm(WINDOW_END, time_cls(10, 0))


def is_configured() -> bool:
    """True, wenn ein API-Key gesetzt ist."""
    return bool(API_KEY)


def in_window(now_local: Optional[datetime] = None) -> bool:
    """Liegt der Zeitpunkt im Aufzeichnungsfenster (lokale Zeit)?"""
    now_local = now_local or datetime.now(_tz())
    t = now_local.time()
    return WINDOW_START_T <= t < WINDOW_END_T


def to_celsius(raw: Optional[float]) -> Optional[float]:
    """Rohwert der API gemäß GOVEE_TEMP_INPUT_UNIT nach Celsius umrechnen."""
    if raw is None:
        return None
    unit = TEMP_INPUT_UNIT
    if unit == "c":
        return round(raw, 2)
    if unit == "f":
        return round((raw - 32) * 5.0 / 9.0, 2)
    # auto: realistische Innenraum-/Kühl-Temperaturen liegen in °C unter ~45.
    # Höhere Werte sind praktisch sicher Fahrenheit.
    if raw > 45:
        return round((raw - 32) * 5.0 / 9.0, 2)
    return round(raw, 2)


# ── Govee-API-Client ──────────────────────────────────────────────────────────

class GoveeClient:
    """Dünner async-Client für die Govee-Cloud-API (v2)."""

    def __init__(self, api_key: str, timeout: float = 15.0):
        self.api_key = api_key
        self._timeout = timeout

    @property
    def _headers(self) -> dict:
        return {
            "Govee-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

    async def list_devices(self) -> list[dict]:
        """Alle Geräte des Accounts. Wirft bei Fehler eine Exception."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.get(DEVICES_URL, headers=self._headers)
            r.raise_for_status()
            data = r.json()
        if data.get("code") not in (200, None):
            raise RuntimeError(f"Govee API code={data.get('code')}: {data.get('message')}")
        return data.get("data", []) or []

    async def get_device_state(self, sku: str, device: str) -> dict:
        """Aktueller Zustand (capabilities) eines Geräts."""
        body = {
            "requestId": str(uuid.uuid4()),
            "payload": {"sku": sku, "device": device},
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.post(STATE_URL, headers=self._headers, json=body)
            r.raise_for_status()
            data = r.json()
        if data.get("code") not in (200, None):
            raise RuntimeError(f"Govee API code={data.get('code')}: {data.get('message')}")
        return data.get("payload", {}) or {}


# ── Parsing-Helfer ──────────────────────────────────────────────────────────

def has_climate_caps(device: dict) -> bool:
    """Hat das Gerät Temperatur-/Feuchte-Capabilities (Thermo-/Hygrometer)?"""
    dtype = (device.get("type") or "").lower()
    if "thermometer" in dtype or "hygrometer" in dtype or "sensor" in dtype:
        return True
    for cap in device.get("capabilities", []) or []:
        inst = cap.get("instance")
        if inst in TEMP_INSTANCES or inst in HUM_INSTANCES:
            return True
    return False


def extract_values(payload: dict) -> dict:
    """Aus einer device/state-Antwort Temperatur, Feuchte, Online ziehen."""
    temp_raw: Optional[float] = None
    humidity: Optional[float] = None
    online: Optional[bool] = None
    for cap in payload.get("capabilities", []) or []:
        inst = cap.get("instance")
        value = (cap.get("state") or {}).get("value")
        if inst in TEMP_INSTANCES and value is not None:
            try:
                temp_raw = float(value)
            except (TypeError, ValueError):
                pass
        elif inst in HUM_INSTANCES and value is not None:
            try:
                humidity = float(value)
            except (TypeError, ValueError):
                pass
        elif inst in ONLINE_INSTANCES:
            online = bool(value)
    return {
        "temp_raw": temp_raw,
        "temp_c": to_celsius(temp_raw),
        "humidity": humidity,
        "online": online,
    }


# ── SQLite-Speicher ───────────────────────────────────────────────────────────

def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_db() -> None:
    """Tabellen + Indizes anlegen (idempotent)."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS readings (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_utc    TEXT NOT NULL,
                ts_local  TEXT NOT NULL,
                day       TEXT NOT NULL,
                device    TEXT NOT NULL,
                sku       TEXT,
                name      TEXT,
                temp_c    REAL,
                temp_raw  REAL,
                humidity  REAL,
                online    INTEGER,
                source    TEXT DEFAULT 'govee',
                battery   REAL
            )
            """
        )
        # Migrationen: fehlende Spalten für bestehende DBs ergänzen (idempotent)
        cols = [r[1] for r in conn.execute("PRAGMA table_info(readings)").fetchall()]
        if "source" not in cols:
            conn.execute("ALTER TABLE readings ADD COLUMN source TEXT DEFAULT 'govee'")
        if "battery" not in cols:
            conn.execute("ALTER TABLE readings ADD COLUMN battery REAL")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_readings_day_device "
            "ON readings(day, device)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_readings_device_ts "
            "ON readings(device, ts_utc)"
        )
        conn.commit()


def insert_reading(
    *, ts_utc: str, ts_local: str, day: str, device: str, sku: str,
    name: str, temp_c: Optional[float], temp_raw: Optional[float],
    humidity: Optional[float], online: Optional[bool], source: str = "govee",
    battery: Optional[float] = None,
) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO readings
              (ts_utc, ts_local, day, device, sku, name,
               temp_c, temp_raw, humidity, online, source, battery)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (ts_utc, ts_local, day, device, sku, name,
             temp_c, temp_raw, humidity,
             None if online is None else int(online), source, battery),
        )
        conn.commit()


def query_history(day: str, device: Optional[str] = None) -> list[dict]:
    """Alle Messwerte eines Tages (optional für ein Gerät), aufsteigend."""
    sql = "SELECT * FROM readings WHERE day = ?"
    params: list[Any] = [day]
    if device:
        sql += " AND device = ?"
        params.append(device)
    sql += " ORDER BY ts_utc ASC"
    with _connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def query_latest_per_device() -> list[dict]:
    """Jeweils neuester Messwert pro Gerät."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT r.* FROM readings r
            JOIN (
              SELECT device, MAX(ts_utc) AS m FROM readings GROUP BY device
            ) last ON r.device = last.device AND r.ts_utc = last.m
            ORDER BY r.name, r.device
            """
        ).fetchall()
    return [dict(r) for r in rows]


def query_days() -> list[str]:
    """Liste aller Tage mit Daten, neueste zuerst."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT day FROM readings ORDER BY day DESC"
        ).fetchall()
    return [r["day"] for r in rows]


def query_devices() -> list[dict]:
    """Bekannte Geräte (aus den gespeicherten Messwerten)."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT device, sku, MAX(name) AS name, COUNT(*) AS n,
                   MIN(day) AS first_day, MAX(day) AS last_day
            FROM readings GROUP BY device, sku ORDER BY name
            """
        ).fetchall()
    return [dict(r) for r in rows]


def query_day_summary(day: str) -> list[dict]:
    """Min/Max/Mittel pro Gerät für einen Tag (Fenster 07–10 Uhr)."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT device, MAX(name) AS name, sku,
                   COUNT(*) AS n,
                   MIN(temp_c) AS temp_min, MAX(temp_c) AS temp_max,
                   AVG(temp_c) AS temp_avg,
                   MIN(humidity) AS hum_min, MAX(humidity) AS hum_max,
                   AVG(humidity) AS hum_avg
            FROM readings WHERE day = ?
            GROUP BY device, sku ORDER BY name
            """,
            (day,),
        ).fetchall()
    return [dict(r) for r in rows]


# ── Poller (Hintergrund-Task) ─────────────────────────────────────────────────

class SensorPoller:
    """Fragt die Govee-API 24/7 zyklisch ab und speichert die Werte."""

    def __init__(self):
        self.client = GoveeClient(API_KEY) if is_configured() else None
        self.last_poll_utc: Optional[str] = None
        self.last_result: str = "noch nicht gelaufen"
        self.last_error: Optional[str] = None
        self.last_device_count: int = 0
        self._devices_cache: Optional[list] = None
        self._devices_cached_at: float = 0.0
        self._task: Optional[asyncio.Task] = None
        self._stop = asyncio.Event()

    # -- öffentliche Status-Info für /api/sensors/status -----------------------
    def status(self) -> dict:
        tz = _tz()
        now = datetime.now(tz)
        return {
            "configured": is_configured(),
            "running": self._task is not None and not self._task.done(),
            "record_mode": "24/7",
            "in_window": in_window(now),
            "window": f"{WINDOW_START}–{WINDOW_END}",
            "timezone": TZ_NAME,
            "poll_interval_sec": POLL_INTERVAL_SEC,
            "temp_input_unit": TEMP_INPUT_UNIT,
            "now_local": now.isoformat(timespec="seconds"),
            "last_poll_utc": self.last_poll_utc,
            "last_result": self.last_result,
            "last_error": self.last_error,
            "last_device_count": self.last_device_count,
            "db_path": str(DB_PATH),
        }

    # -- Geräteliste (gecacht, alle 30 min neu) --------------------------------
    async def _get_devices(self) -> list:
        now = time.monotonic()
        if (self._devices_cache is None
                or now - self._devices_cached_at > DEVICE_REFRESH_SEC):
            self._devices_cache = await self.client.list_devices()
            self._devices_cached_at = now
        return self._devices_cache

    # -- ein einzelner Mess-Durchlauf ------------------------------------------
    async def poll_once(self) -> int:
        """Liest alle Klima-Sensoren und speichert deren Werte. Gibt Anzahl zurück."""
        if not self.client:
            return 0
        tz = _tz()
        now = datetime.now(tz)
        now_utc = datetime.now(timezone.utc)
        ts_utc = now_utc.isoformat(timespec="seconds")
        ts_local = now.isoformat(timespec="seconds")
        day = now.strftime("%Y-%m-%d")

        devices = await self._get_devices()
        climate = [d for d in devices if has_climate_caps(d)]
        self.last_device_count = len(climate)

        stored = 0
        for dev in climate:
            sku = dev.get("sku", "")
            device_id = dev.get("device", "")
            name = dev.get("deviceName") or dev.get("name") or sku or device_id
            try:
                payload = await self.client.get_device_state(sku, device_id)
                vals = extract_values(payload)
            except Exception as e:  # einzelnes Gerät überspringen
                print(f"[govee] Status-Fehler {name}: {e}")
                continue
            if vals["temp_raw"] is None and vals["humidity"] is None:
                continue  # keine verwertbaren Werte
            await asyncio.to_thread(
                insert_reading,
                ts_utc=ts_utc, ts_local=ts_local, day=day,
                device=device_id, sku=sku, name=name,
                temp_c=vals["temp_c"], temp_raw=vals["temp_raw"],
                humidity=vals["humidity"], online=vals["online"],
            )
            stored += 1
        self.last_poll_utc = ts_utc
        return stored

    # -- Dauerschleife (24/7-Aufzeichnung) -------------------------------------
    async def _run(self) -> None:
        await asyncio.to_thread(init_db)
        print(f"[govee] Poller gestartet · 24/7-Aufzeichnung · "
              f"Intervall {POLL_INTERVAL_SEC}s · DB {DB_PATH}")
        while not self._stop.is_set():
            now = datetime.now(_tz())
            try:
                n = await self.poll_once()
                self.last_result = f"ok – {n} Sensor(en) gespeichert"
                self.last_error = None
                print(f"[govee] {now:%Y-%m-%d %H:%M:%S} – {n} Sensor(en) gespeichert")
            except Exception as e:
                self.last_result = "Fehler"
                self.last_error = str(e)
                print(f"[govee] Poll-Fehler: {e}")
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=POLL_INTERVAL_SEC)
            except asyncio.TimeoutError:
                pass

    def start(self) -> None:
        if not is_configured():
            print("[govee] GOVEE_API_KEY fehlt – Poller deaktiviert.")
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
