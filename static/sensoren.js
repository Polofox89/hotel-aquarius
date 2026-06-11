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
  mode: "full",         // "full" = 24 Stunden | "control" = Kontrolle 7-10 Uhr
  windowStart: 7,       // Kontroll-Fenster Beginn (Stunde)
  windowEnd: 10,        // Kontroll-Fenster Ende (Stunde)
  readings: [],         // Messwerte des aktuell geladenen Tages
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
      document.getElementById("modeControl").textContent = `🔍 Kontrolle ${state.windowStart}–${state.windowEnd} Uhr`;
    }

    if (!s.configured) {
      banner.innerHTML = "⚠️ <b>Kein API-Key gesetzt.</b> Setze die Umgebungsvariable " +
        "<code>GOVEE_API_KEY</code> auf dem Server, dann beginnt die Aufzeichnung " +
        "automatisch (24/7).";
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
        ${r.battery != null ? `<div class="battery${r.battery <= 20 ? " low" : ""}">🔋 ${fmt(r.battery, 0)} %</div>` : ""}
        <div class="meta">Letzte Messung: ${when}</div>
      </div>`;
  }).join("");
}

// ── Diagramme ─────────────────────────────────────────────────────────────────

// Rote horizontale Grenzlinie (z. B. 7 °C Kühlgrenze) – schlankes Chart.js-Plugin
const thresholdLinePlugin = {
  id: "thresholdLine",
  afterDatasetsDraw(chart, args, opts) {
    if (!opts || opts.value == null) return;
    const yScale = chart.scales.y, area = chart.chartArea, ctx = chart.ctx;
    if (!yScale || !area) return;
    const yPix = yScale.getPixelForValue(opts.value);
    if (yPix < area.top || yPix > area.bottom) return;  // außerhalb sichtbar → nicht zeichnen
    ctx.save();
    ctx.beginPath();
    ctx.setLineDash([6, 4]);
    ctx.lineWidth = 2;
    ctx.strokeStyle = opts.color || "#c62828";
    ctx.moveTo(area.left, yPix);
    ctx.lineTo(area.right, yPix);
    ctx.stroke();
    if (opts.label) {
      ctx.setLineDash([]);
      ctx.fillStyle = opts.color || "#c62828";
      ctx.font = "12px 'Segoe UI', system-ui, sans-serif";
      ctx.textAlign = "right";
      ctx.textBaseline = "bottom";
      ctx.fillText(opts.label, area.right - 6, yPix - 3);
    }
    ctx.restore();
  },
};

function buildChart(canvasId, label, unit, datasets, hMin, hMax) {
  const span = hMax - hMin;
  const stepSize = span <= 4 ? 0.5 : (span <= 12 ? 1 : 2);
  const ctx = document.getElementById(canvasId).getContext("2d");
  const config = {
    type: "line",
    data: { datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "nearest", intersect: false },
      scales: {
        x: {
          type: "linear",
          min: hMin,
          max: hMax,
          title: { display: true, text: "Uhrzeit" },
          ticks: {
            stepSize: stepSize,
            maxRotation: 0,
            autoSkip: true,
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
  };
  // Rote Grenzlinie bei 7 °C – nur im Temperatur-Chart
  if (unit === "°C") {
    config.plugins = [thresholdLinePlugin];
    config.options.plugins.thresholdLine = { value: 7, color: "#c62828", label: "Grenze 7 °C" };
  }
  return new Chart(ctx, config);
}

// Bestehendes Chart in-place aktualisieren (Achsenbereich + Daten) und dabei
// den Legenden-Filter erhalten; existiert noch keins, neu anlegen.
function upsertChart(chart, canvasId, label, unit, datasets, hMin, hMax) {
  if (!chart) return buildChart(canvasId, label, unit, datasets, hMin, hMax);
  // Ausgeblendete Sensoren je Name merken
  const hidden = {};
  chart.data.datasets.forEach((ds, i) => { hidden[ds.label] = !chart.isDatasetVisible(i); });
  // Achsenbereich an den Modus anpassen (24 h ↔ 7–10 Uhr)
  const span = hMax - hMin;
  chart.options.scales.x.min = hMin;
  chart.options.scales.x.max = hMax;
  chart.options.scales.x.ticks.stepSize = span <= 4 ? 0.5 : (span <= 12 ? 1 : 2);
  // Daten ersetzen, ohne Animation
  chart.data.datasets = datasets;
  chart.update("none");
  // Filter (per Name) wieder anwenden
  chart.data.datasets.forEach((ds, i) => {
    if (hidden[ds.label]) chart.setDatasetVisibility(i, false);
  });
  chart.update("none");
  return chart;
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
    const data = info.points.filter((p) => p.y !== null && p.y !== undefined);
    return {
      label: info.name,
      data,
      borderColor: color,
      backgroundColor: color + "33",
      tension: 0.3,
      pointRadius: data.length > 150 ? 0 : 2,
      borderWidth: 2,
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
  state.readings = data.readings || [];
  renderView();
}

// Zeichnet Charts + Zusammenfassung je nach gewählter Ansicht (24 h oder 7–10 Uhr)
function renderView() {
  const [hMin, hMax] = state.mode === "control"
    ? [state.windowStart, state.windowEnd]
    : [0, 24];
  const inRange = (state.readings || []).filter((r) => {
    const h = decimalHour(r.ts_local);
    return h >= hMin && h < hMax;
  });
  const hasData = inRange.length > 0;

  // Feuchte nur anzeigen, wenn mindestens ein Sensor Feuchte-Werte liefert
  const hasHum = inRange.some((r) => r.humidity !== null && r.humidity !== undefined);
  document.body.classList.toggle("no-humidity", !hasHum);

  if (typeof Chart === "undefined") return;  // CDN noch nicht geladen
  document.getElementById("tempEmpty").style.display = hasData ? "none" : "flex";
  document.getElementById("humEmpty").style.display = hasData ? "none" : "flex";

  // Charts aktualisieren statt neu bauen → Legenden-Filter (ausgeblendete
  // Sensoren) bleibt beim Auto-Refresh / Moduswechsel erhalten.
  tempChart = upsertChart(tempChart, "tempChart", "Temperatur", "°C", datasetsFor(inRange, "temp_c"), hMin, hMax);
  if (hasHum) {
    humChart = upsertChart(humChart, "humChart", "Luftfeuchte", "%", datasetsFor(inRange, "humidity"), hMin, hMax);
  } else if (humChart) {
    humChart.destroy();
    humChart = null;
  }

  // Überschrift der Zusammenfassung an die Ansicht anpassen
  document.getElementById("summaryTitle").textContent =
    state.mode === "control" ? `Frühstückszeit (${hMin}–${hMax} Uhr)` : "Tages-Zusammenfassung";
  renderSummary(computeSummary(inRange));
}

// Min/Max/Mittel je Gerät aus den (gefilterten) Messwerten berechnen
function computeSummary(readings) {
  const by = {};
  readings.forEach((r) => {
    const g = by[r.device] || (by[r.device] =
      { device: r.device, sku: r.sku, name: r.name || r.device, temps: [], hums: [] });
    if (r.temp_c !== null && r.temp_c !== undefined) g.temps.push(r.temp_c);
    if (r.humidity !== null && r.humidity !== undefined) g.hums.push(r.humidity);
  });
  const stat = (arr) => arr.length
    ? { min: Math.min(...arr), max: Math.max(...arr), avg: arr.reduce((a, b) => a + b, 0) / arr.length }
    : { min: null, max: null, avg: null };
  return Object.values(by).map((g) => {
    const t = stat(g.temps), h = stat(g.hums);
    return {
      device: g.device, name: g.name, sku: g.sku,
      n: Math.max(g.temps.length, g.hums.length),
      temp_avg: t.avg, temp_min: t.min, temp_max: t.max,
      hum_avg: h.avg, hum_min: h.min, hum_max: h.max,
    };
  }).sort((a, b) => (a.name || "").localeCompare(b.name || ""));
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

// Ansicht umschalten (ohne Neuladen der Daten) – nur eine Ansicht aktiv
function setMode(mode) {
  state.mode = mode;
  document.getElementById("modeFull").classList.toggle("active", mode === "full");
  document.getElementById("modeControl").classList.toggle("active", mode === "control");
  renderView();
}

function wireControls() {
  document.getElementById("prevDay").onclick = () => shiftDay(-1);
  document.getElementById("nextDay").onclick = () => shiftDay(1);
  document.getElementById("todayBtn").onclick = () => { state.day = todayISO(); loadDay(); };
  document.getElementById("dayPicker").onchange = (e) => {
    if (e.target.value) { state.day = e.target.value; loadDay(); }
  };
  document.getElementById("modeFull").onclick = () => setMode("full");
  document.getElementById("modeControl").onclick = () => setMode("control");
  document.getElementById("showAllBtn").onclick = showAllDatasets;
}

// Alle ausgeblendeten Sensoren in beiden Diagrammen wieder einblenden
function showAllDatasets() {
  [tempChart, humChart].forEach((ch) => {
    if (!ch) return;
    ch.data.datasets.forEach((ds, i) => ch.setDatasetVisibility(i, true));
    ch.update("none");
  });
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
