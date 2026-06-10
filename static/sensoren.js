/* ════════════════════════════════════════════════════════════════════════════
   Sensor-Dashboard · Hotel Aquarius
   Holt Govee-Messwerte vom Backend und stellt sie grafisch dar.
   Aufzeichnung/Anzeige nur im Zeitfenster 07:00–10:00 Uhr.
   ══════════════════════════════════════════════════════════════════════════ */

"use strict";

// Farbpalette pro Sensor (Aquarius-Teal + gut unterscheidbare Begleitfarben)
const PALETTE = ["#1A8C96", "#e07b39", "#5b8def", "#9b59b6", "#2e7d32",
                 "#c62828", "#0097a7", "#f39c12"];

const state = {
  day: null,            // YYYY-MM-DD
  windowStart: 7,       // Stunde
  windowEnd: 10,
  deviceColors: {},     // device-id → Farbe
};

let tempChart = null;
let humChart = null;

// ── Hilfsfunktionen ───────────────────────────────────────────────────────────

async function fetchJSON(url) {
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) throw new Error(`${url} → HTTP ${r.status}`);
  return r.json();
}

function todayISO() {
  // Lokales Datum (Browser-Zeit; Hotel steht in DE → passt zu Europe/Berlin)
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function colorFor(deviceId, index) {
  if (!state.deviceColors[deviceId]) {
    state.deviceColors[deviceId] = PALETTE[index % PALETTE.length];
  }
  return state.deviceColors[deviceId];
}

// "2026-06-10T07:32:00+02:00" → 7.533 (Dezimalstunde, lokale Zeit)
function decimalHour(tsLocal) {
  const hh = parseInt(tsLocal.slice(11, 13), 10);
  const mm = parseInt(tsLocal.slice(14, 16), 10);
  return hh + mm / 60;
}

function fmt(v, digits = 1) {
  return (v === null || v === undefined || Number.isNaN(v)) ? "–" : Number(v).toFixed(digits);
}

// ── Status / Konfiguration ──────────────────────────────────────────────────

async function loadStatus() {
  const banner = document.getElementById("banner");
  try {
    const s = await fetchJSON("/api/sensors/status");
    // Fensterzeiten robust übernehmen (En-Dash ODER Bindestrich, beliebige Trenner)
    const m = (s.window || "").match(/(\d{1,2}):\d{2}\D+(\d{1,2}):\d{2}/);
    if (m) {
      state.windowStart = parseInt(m[1], 10);
      state.windowEnd = parseInt(m[2], 10);
    }
    document.getElementById("windowPill").textContent = `Aufzeichnung ${s.window || "07:00–10:00"} Uhr`;

    if (!s.configured) {
      banner.innerHTML = "⚠️ <b>Kein API-Key gesetzt.</b> Setze die Umgebungsvariable " +
        "<code>GOVEE_API_KEY</code> auf dem Server, dann beginnt die Aufzeichnung " +
        "automatisch im Zeitfenster.";
      banner.classList.add("show");
    } else if (s.last_error) {
      banner.innerHTML = `⚠️ Letzter Abruf-Fehler: <code>${s.last_error}</code>`;
      banner.classList.add("show");
    } else {
      banner.classList.remove("show");
    }
  } catch (e) {
    banner.innerHTML = `⚠️ Status konnte nicht geladen werden: ${e.message}`;
    banner.classList.add("show");
  }
}

// ── Live-Kacheln ──────────────────────────────────────────────────────────────

async function loadLatest() {
  const box = document.getElementById("tiles");
  let latest;
  try {
    latest = await fetchJSON("/api/sensors/latest");
  } catch (e) {
    box.innerHTML = `<div class="tile"><div class="meta">Fehler: ${e.message}</div></div>`;
    return;
  }
  if (!latest.length) {
    box.innerHTML = '<div class="tile"><div class="meta">Noch keine Messwerte. ' +
      'Werte werden im Zeitfenster 07:00–10:00 Uhr aufgezeichnet.</div></div>';
    return;
  }
  box.innerHTML = latest.map((r, i) => {
    const color = colorFor(r.device, i);
    const onlineCls = r.online === 1 ? "online" : (r.online === 0 ? "offline" : "");
    const when = r.ts_local ? r.ts_local.slice(0, 16).replace("T", " ") : "";
    return `
      <div class="tile" style="border-top-color:${color}">
        <div class="name"><span class="dot ${onlineCls}"></span>${r.name || r.device}</div>
        <div class="readout">
          <span class="temp">${fmt(r.temp_c)}<span class="unit"> °C</span></span>
          ${r.humidity != null ? `<span class="hum">${fmt(r.humidity, 0)}<span class="unit"> % rF</span></span>` : ""}
        </div>
        <div class="meta">Letzte Messung: ${when}</div>
      </div>`;
  }).join("");
}

// ── Diagramme ─────────────────────────────────────────────────────────────────

function buildChart(canvasId, label, unit, datasets) {
  const ctx = document.getElementById(canvasId).getContext("2d");
  return new Chart(ctx, {
    type: "line",
    data: { datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "nearest", intersect: false },
      scales: {
        x: {
          type: "linear",
          min: state.windowStart,
          max: state.windowEnd,
          title: { display: true, text: "Uhrzeit" },
          ticks: {
            stepSize: 0.5,
            callback: (v) => {
              const h = Math.floor(v);
              const m = Math.round((v - h) * 60);
              return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
            },
          },
        },
        y: { title: { display: true, text: `${label} (${unit})` } },
      },
      plugins: {
        legend: { position: "bottom" },
        tooltip: {
          callbacks: {
            title: (items) => {
              const v = items[0].parsed.x;
              const h = Math.floor(v);
              const m = Math.round((v - h) * 60);
              return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")} Uhr`;
            },
            label: (it) => `${it.dataset.label}: ${fmt(it.parsed.y)} ${unit}`,
          },
        },
      },
    },
  });
}

function datasetsFor(readings, field) {
  // Nach Gerät gruppieren
  const byDevice = {};
  readings.forEach((r) => {
    (byDevice[r.device] = byDevice[r.device] || { name: r.name || r.device, points: [] })
      .points.push({ x: decimalHour(r.ts_local), y: r[field] });
  });
  let i = 0;
  return Object.entries(byDevice).map(([device, info]) => {
    const color = colorFor(device, i++);
    return {
      label: info.name,
      data: info.points.filter((p) => p.y !== null && p.y !== undefined),
      borderColor: color,
      backgroundColor: color + "33",
      tension: 0.3,
      pointRadius: 2,
      spanGaps: true,
    };
  });
}

// ── Tages-Daten laden ──────────────────────────────────────────────────────────

async function loadDay() {
  document.getElementById("dayPicker").value = state.day;
  let data;
  try {
    data = await fetchJSON(`/api/sensors/history?day=${state.day}`);
  } catch (e) {
    return;
  }
  const readings = data.readings || [];
  const hasData = readings.length > 0;

  // Feuchte nur anzeigen, wenn mindestens ein Sensor Feuchte-Werte liefert
  const hasHum = readings.some((r) => r.humidity !== null && r.humidity !== undefined);
  document.body.classList.toggle("no-humidity", !hasHum);

  // Charts
  if (typeof Chart === "undefined") return;  // CDN noch nicht geladen
  document.getElementById("tempEmpty").style.display = hasData ? "none" : "flex";
  document.getElementById("humEmpty").style.display = hasData ? "none" : "flex";

  if (tempChart) tempChart.destroy();
  if (humChart) { humChart.destroy(); humChart = null; }
  tempChart = buildChart("tempChart", "Temperatur", "°C", datasetsFor(readings, "temp_c"));
  if (hasHum) {
    humChart = buildChart("humChart", "Luftfeuchte", "%", datasetsFor(readings, "humidity"));
  }

  renderSummary(data.summary || []);
}

function renderSummary(summary) {
  const tbody = document.querySelector("#summaryTable tbody");
  if (!summary.length) {
    tbody.innerHTML = '<tr><td colspan="8">Keine Daten für diesen Tag.</td></tr>';
    return;
  }
  tbody.innerHTML = summary.map((s, i) => {
    const color = colorFor(s.device, i);
    return `<tr>
      <td><span class="swatch" style="background:${color}"></span>${s.name || s.device}</td>
      <td>${fmt(s.temp_avg)} °C</td>
      <td>${fmt(s.temp_min)} °C</td>
      <td>${fmt(s.temp_max)} °C</td>
      <td class="hum-col">${fmt(s.hum_avg, 0)} %</td>
      <td class="hum-col">${fmt(s.hum_min, 0)} %</td>
      <td class="hum-col">${fmt(s.hum_max, 0)} %</td>
      <td>${s.n}</td>
    </tr>`;
  }).join("");
}

// ── Navigation ──────────────────────────────────────────────────────────────

function shiftDay(deltaDays) {
  const d = new Date(state.day + "T12:00:00");
  d.setDate(d.getDate() + deltaDays);
  state.day = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  loadDay();
}

function wireControls() {
  document.getElementById("prevDay").onclick = () => shiftDay(-1);
  document.getElementById("nextDay").onclick = () => shiftDay(1);
  document.getElementById("todayBtn").onclick = () => { state.day = todayISO(); loadDay(); };
  document.getElementById("dayPicker").onchange = (e) => {
    if (e.target.value) { state.day = e.target.value; loadDay(); }
  };
}

// ── Auto-Refresh (nur wenn „heute" angezeigt wird) ────────────────────────────

function startAutoRefresh() {
  setInterval(() => {
    loadLatest();
    if (state.day === todayISO()) loadDay();
  }, 60000);
}

// ── Init ──────────────────────────────────────────────────────────────────────

async function init() {
  state.day = todayISO();
  wireControls();
  await loadStatus();
  await loadLatest();
  // kurz warten, bis Chart.js (defer) geladen ist
  if (typeof Chart === "undefined") {
    await new Promise((res) => window.addEventListener("load", res, { once: true }));
  }
  await loadDay();
  startAutoRefresh();
}

init();
