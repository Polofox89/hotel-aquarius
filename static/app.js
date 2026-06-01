// ════════════════════════════════════════════════════════════════════════════
// Tagesbuffet Web-App – Frontend
// ════════════════════════════════════════════════════════════════════════════

const API = ""; // relative URL → gleiches Origin wie das HTML

const STATE = {
  date: new Date(),
  categories: [],
  slots: [],
  suggestions: {},
  lastPreviewBlobUrl: null,
  renderTimer: null,
};

const WEEKDAYS_DE = ["Sonntag","Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag"];
const MONTHS_DE   = ["Januar","Februar","März","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"];


// ── Helpers ────────────────────────────────────────────────────────────────

function isoDate(d) {
  // YYYY-MM-DD (lokal, ohne TZ-Verschiebung)
  return d.getFullYear() + "-" +
         String(d.getMonth() + 1).padStart(2, "0") + "-" +
         String(d.getDate()).padStart(2, "0");
}

function formatDateDE(d) {
  return `${WEEKDAYS_DE[d.getDay()]}, ${String(d.getDate()).padStart(2,"0")}. ${MONTHS_DE[d.getMonth()]} ${d.getFullYear()}`;
}

function setStatus(msg, level = "info") {
  const el = document.getElementById("status");
  el.textContent = msg;
  el.className = "status " + level;
}

// Status mit anklickbarem Link (z. B. Dateiname → Bild öffnen)
function setStatusLink(prefix, linkText, url, level = "success") {
  const el = document.getElementById("status");
  el.className = "status " + level;
  el.textContent = prefix;              // statischer Teil (XSS-sicher)
  const a = document.createElement("a");
  a.href = url;
  a.target = "_blank";
  a.rel = "noopener";
  a.textContent = linkText;             // Dateiname als Linktext
  a.className = "saved-link";
  el.appendChild(a);
}

function debounce(fn, delay) {
  let t = null;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), delay);
  };
}


// ── Datum-Handling ─────────────────────────────────────────────────────────

function setDate(d) {
  STATE.date = d;
  document.getElementById("date-input").value = isoDate(d);
  document.getElementById("date-display").textContent = formatDateDE(d);
  scheduleRender();
}


// ── Slots dynamisch rendern ────────────────────────────────────────────────

function renderSlots() {
  const container = document.getElementById("slots");
  if (!container || STATE.slots.length === 0) return;

  // Aktuelle Werte sichern, falls schon ausgefüllt
  const current = {};
  container.querySelectorAll("input[data-slot]").forEach(inp => {
    current[inp.dataset.slot] = inp.value;
  });

  container.innerHTML = "";

  // Zähler pro Kategorie (für Nummerierung "Hauptgericht 1/2")
  const counters = {};

  STATE.slots.forEach(slot => {
    counters[slot.category] = (counters[slot.category] || 0) + 1;
    const n = counters[slot.category];

    const labelBase = I18N.t("cat_" + slot.category);
    // Bei Kategorien mit mehreren Slots: Nummer anhängen
    const totalInCat = STATE.slots.filter(s => s.category === slot.category).length;
    const label = totalInCat > 1 ? `${labelBase} ${n}` : labelBase;

    const row = document.createElement("div");
    row.className = "slot-row";

    const labelEl = document.createElement("div");
    labelEl.className = "slot-label";
    labelEl.textContent = label;
    if (slot.optional) {
      const span = document.createElement("span");
      span.className = "optional";
      span.textContent = " " + I18N.t("optional");
      labelEl.appendChild(span);
    }
    row.appendChild(labelEl);

    const inputWrap = document.createElement("div");
    inputWrap.className = "slot-input";
    const input = document.createElement("input");
    input.type = "text";
    input.dataset.slot = slot.slot;
    input.dataset.category = slot.category;
    input.setAttribute("list", `datalist-${slot.category}`);
    input.value = current[slot.slot] || "";
    input.addEventListener("input", scheduleRender);
    inputWrap.appendChild(input);

    // Datalist (Native Browser-Dropdown mit Autocomplete) – nur einmal pro Kategorie
    if (!document.getElementById(`datalist-${slot.category}`)) {
      const dl = document.createElement("datalist");
      dl.id = `datalist-${slot.category}`;
      (STATE.suggestions[slot.category] || []).forEach(name => {
        const opt = document.createElement("option");
        opt.value = name;
        dl.appendChild(opt);
      });
      inputWrap.appendChild(dl);
    }

    row.appendChild(inputWrap);
    container.appendChild(row);
  });

  applyDefaults();
}

// Defaults für Salate / Dessert / Partypfanne setzen, falls leer
function applyDefaults() {
  STATE.slots.forEach(slot => {
    const cat = STATE.categories.find(c => c.key === slot.category);
    if (!cat || !cat.defaults || cat.defaults.length === 0) return;
    const inp = document.querySelector(`input[data-slot="${slot.slot}"]`);
    if (inp && !inp.value) inp.value = cat.defaults[slot.index] || "";
  });
}


// ── Menü aus Inputs einsammeln ─────────────────────────────────────────────

function collectMenu() {
  const menu = {};
  STATE.categories.forEach(c => menu[c.key] = []);

  document.querySelectorAll("input[data-slot]").forEach(inp => {
    const v = inp.value.trim();
    if (v) menu[inp.dataset.category].push(v);
  });

  return menu;
}


// ── Vorschau rendern (debounced) ───────────────────────────────────────────

const scheduleRender = debounce(renderPreview, 350);

async function renderPreview() {
  const menu = collectMenu();
  const payload = { date: isoDate(STATE.date), menu };

  const loading = document.getElementById("preview-loading");
  loading.classList.add("active");

  try {
    const res = await fetch(`${API}/api/preview`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(err || res.statusText);
    }
    const blob = await res.blob();
    if (STATE.lastPreviewBlobUrl) URL.revokeObjectURL(STATE.lastPreviewBlobUrl);
    STATE.lastPreviewBlobUrl = URL.createObjectURL(blob);
    document.getElementById("preview-img").src = STATE.lastPreviewBlobUrl;
    setStatus(I18N.t("ready"), "info");
  } catch (e) {
    console.error(e);
    setStatus(I18N.t("err_render") + ": " + e.message, "error");
  } finally {
    loading.classList.remove("active");
  }
}


// ── Speichern ──────────────────────────────────────────────────────────────

async function saveMenu() {
  const menu = collectMenu();
  const payload = { date: isoDate(STATE.date), menu };

  const btn = document.getElementById("btn-save");
  btn.disabled = true;
  setStatus(I18N.t("saving"), "info");

  try {
    const res = await fetch(`${API}/api/save`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(await res.text() || res.statusText);
    const data = await res.json();
    // Dateiname als Link anzeigen → öffnet das gespeicherte Bild in neuem Tab
    setStatusLink(`${I18N.t("saved")}: `, data.saved, data.url, "success");
    loadHistory();
  } catch (e) {
    console.error(e);
    setStatus(I18N.t("err_save") + ": " + e.message, "error");
  } finally {
    btn.disabled = false;
  }
}


// ── KI-Analyse ─────────────────────────────────────────────────────────────

async function runKiAnalyze() {
  const text = document.getElementById("ki-text").value.trim();
  if (!text) {
    setStatus(I18N.t("err_no_text"), "error");
    return;
  }

  const btn = document.getElementById("btn-ki");
  const originalLabel = btn.textContent;
  btn.disabled = true;
  btn.textContent = I18N.t("ki_running");
  setStatus(I18N.t("ki_running"), "info");

  try {
    const res = await fetch(`${API}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (res.status === 503) {
      throw new Error(I18N.t("err_ki_off"));
    }
    if (!res.ok) throw new Error(await res.text() || res.statusText);
    const data = await res.json();

    // Menü in die Slots eintragen
    fillSlotsFromMenu(data.menu);
    setStatus("✓ KI", "success");
    scheduleRender();
  } catch (e) {
    console.error(e);
    setStatus(I18N.t("err_ki") + ": " + e.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = originalLabel;
  }
}

function fillSlotsFromMenu(menu) {
  // Slots zuerst leeren
  document.querySelectorAll("input[data-slot]").forEach(inp => inp.value = "");

  // Pro Kategorie: Slots in Reihenfolge füllen
  STATE.categories.forEach(c => {
    const items = menu[c.key] || [];
    const slotsForCat = STATE.slots.filter(s => s.category === c.key);
    slotsForCat.forEach((slot, idx) => {
      if (idx < items.length) {
        const inp = document.querySelector(`input[data-slot="${slot.slot}"]`);
        if (inp) inp.value = items[idx];
      }
    });
  });
}


// ── Verlauf ────────────────────────────────────────────────────────────────

async function loadHistory() {
  const list = document.getElementById("history-list");
  try {
    const res = await fetch(`${API}/api/history?limit=7`);
    if (!res.ok) return;
    const items = await res.json();
    list.innerHTML = "";
    if (items.length === 0) {
      list.innerHTML = `<div class="history-item" style="cursor:default">Noch keine Einträge.</div>`;
      return;
    }
    items.forEach(entry => {
      const haupt = (entry.menu?.haupt || []).slice(0, 2).join(", ");
      const div = document.createElement("div");
      div.className = "history-item";
      div.innerHTML = `
        <div class="history-date">${entry.weekday.slice(0,2)} · ${entry.date}</div>
        <div class="history-preview">${haupt || "–"}</div>
      `;
      div.addEventListener("click", () => loadHistoryEntry(entry));
      list.appendChild(div);
    });
  } catch (e) {
    console.error(e);
  }
}

function loadHistoryEntry(entry) {
  const [d, m, y] = entry.date.split(".");
  setDate(new Date(parseInt(y), parseInt(m) - 1, parseInt(d)));
  fillSlotsFromMenu(entry.menu || {});
  scheduleRender();
}


// ── Initialisierung ────────────────────────────────────────────────────────

window.renderSlots = renderSlots; // i18n.js kann darauf zugreifen

async function init() {
  I18N.init();

  // Categories + Slots vom Backend holen
  try {
    const [catRes, sugRes] = await Promise.all([
      fetch(`${API}/api/categories`),
      fetch(`${API}/api/suggestions`),
    ]);
    const catData = await catRes.json();
    STATE.categories  = catData.categories;
    STATE.slots       = catData.slots;
    STATE.suggestions = await sugRes.json();
  } catch (e) {
    console.error("Init-Fehler:", e);
    setStatus("Backend nicht erreichbar: " + e.message, "error");
    return;
  }

  // Datum init
  setDate(new Date());
  document.getElementById("date-input").addEventListener("change", e => {
    const v = e.target.value;
    if (v) setDate(new Date(v + "T00:00:00"));
  });
  document.getElementById("btn-today").addEventListener("click", () => setDate(new Date()));
  document.getElementById("btn-tomorrow").addEventListener("click", () => {
    const t = new Date();
    t.setDate(t.getDate() + 1);
    setDate(t);
  });

  // Buttons
  document.getElementById("btn-ki").addEventListener("click", runKiAnalyze);
  document.getElementById("btn-save").addEventListener("click", saveMenu);

  // Slots aufbauen + erste Vorschau
  renderSlots();
  loadHistory();
  scheduleRender();

  setStatus(I18N.t("ready"), "info");
}

document.addEventListener("DOMContentLoaded", init);
