/* Hotel Aquarius – Großflächiger Timer (analog & digital)
 *
 * Funktionen:
 *  - Analoge Anzeige (SVG-Zifferblatt mit ablaufendem Bogen + sweepender Zeiger)
 *  - Digitale Anzeige (HH:MM:SS bzw. MM:SS)
 *  - Sekundengenau einstellbar, Voreinstellung 10 Minuten
 *  - Kleiner Ping alle 30 Sekunden
 *  - Jingle beim Erreichen von Null
 *
 * Die verbleibende Zeit wird aus der realen Uhr (performance.now) berechnet,
 * damit der Timer auch über lange Laufzeiten driftfrei bleibt.
 */
(() => {
  "use strict";

  const DEFAULT_SECONDS = 600; // 10 Minuten voreingestellt
  const PING_INTERVAL = 30;    // Ping alle 30 Sekunden
  const WARN_AT = 60;          // Warnphase ab 60 s (gelb)
  const DANGER_AT = 10;        // Endphase ab 10 s (rot)
  const RADIUS = 92;
  const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

  // ---------- DOM ----------
  const el = {
    digital: document.getElementById("digital"),
    status: document.getElementById("status"),
    progress: document.querySelector(".clock__progress"),
    hand: document.getElementById("clockHand"),
    ticks: document.getElementById("clockTicks"),
    startPause: document.getElementById("startPause"),
    reset: document.getElementById("reset"),
    fullscreen: document.getElementById("fullscreen"),
    mute: document.getElementById("mute"),
    inHours: document.getElementById("inHours"),
    inMinutes: document.getElementById("inMinutes"),
    inSeconds: document.getElementById("inSeconds"),
    applyTime: document.getElementById("applyTime"),
    presets: Array.from(document.querySelectorAll(".preset")),
  };

  // ---------- Zustand ----------
  const state = {
    totalSeconds: DEFAULT_SECONDS,   // eingestellte Gesamtzeit
    remaining: DEFAULT_SECONDS,      // verbleibende Zeit (Sekunden, fraktional)
    running: false,
    finished: false,
    muted: false,
    endTime: 0,            // performance.now()-Zeitstempel des Nullpunkts
    rafId: 0,
    lastPingSecond: null,  // zuletzt "gepingte" volle Sekunde (Mehrfach-Pings vermeiden)
  };

  // ---------- Audio (Web Audio API – keine externen Dateien) ----------
  let audioCtx = null;

  function ensureAudio() {
    if (state.muted) return null;
    if (!audioCtx) {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) return null;
      audioCtx = new Ctx();
    }
    if (audioCtx.state === "suspended") audioCtx.resume();
    return audioCtx;
  }

  /** Einzelner Ton mit sanfter Hüllkurve. */
  function tone(freq, start, duration, peak = 0.25, type = "sine") {
    const ctx = audioCtx;
    if (!ctx) return;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = type;
    osc.frequency.value = freq;
    const t0 = ctx.currentTime + start;
    gain.gain.setValueAtTime(0.0001, t0);
    gain.gain.exponentialRampToValueAtTime(peak, t0 + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.0001, t0 + duration);
    osc.connect(gain).connect(ctx.destination);
    osc.start(t0);
    osc.stop(t0 + duration + 0.05);
  }

  /** Kleiner, dezenter Ping. */
  function playPing() {
    if (!ensureAudio()) return;
    tone(880, 0, 0.18, 0.2, "sine");
  }

  /** Jingle beim Erreichen von Null (kleine aufsteigende Melodie + Akkord). */
  function playJingle() {
    if (!ensureAudio()) return;
    const notes = [523.25, 659.25, 783.99, 1046.5]; // C5 E5 G5 C6
    notes.forEach((f, i) => tone(f, i * 0.16, 0.32, 0.28, "triangle"));
    // Abschluss-Akkord
    tone(523.25, 0.7, 0.9, 0.18, "sine");
    tone(783.99, 0.7, 0.9, 0.18, "sine");
    tone(1046.5, 0.7, 0.9, 0.18, "sine");
  }

  // ---------- Hilfsfunktionen ----------
  function clamp(n, min, max) { return Math.min(max, Math.max(min, n)); }

  function formatTime(totalSec) {
    const s = Math.max(0, Math.ceil(totalSec));
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = s % 60;
    const pad = (n) => String(n).padStart(2, "0");
    return h > 0 ? `${pad(h)}:${pad(m)}:${pad(sec)}` : `${pad(m)}:${pad(sec)}`;
  }

  // ---------- Zifferblatt ----------
  function buildTicks() {
    const ns = "http://www.w3.org/2000/svg";
    const frag = document.createDocumentFragment();
    for (let i = 0; i < 60; i++) {
      const major = i % 5 === 0;
      const angle = (i / 60) * 2 * Math.PI;
      const outer = RADIUS - 4;
      const inner = RADIUS - (major ? 14 : 9);
      const line = document.createElementNS(ns, "line");
      line.setAttribute("x1", (100 + Math.sin(angle) * outer).toFixed(2));
      line.setAttribute("y1", (100 - Math.cos(angle) * outer).toFixed(2));
      line.setAttribute("x2", (100 + Math.sin(angle) * inner).toFixed(2));
      line.setAttribute("y2", (100 - Math.cos(angle) * inner).toFixed(2));
      if (major) line.classList.add("major");
      frag.appendChild(line);
    }
    el.ticks.appendChild(frag);
    el.progress.style.strokeDasharray = String(CIRCUMFERENCE);
  }

  // ---------- Render ----------
  function render() {
    const remaining = state.remaining;

    // Digital
    el.digital.textContent = formatTime(remaining);

    // Fortschrittsbogen (voll = ganze Zeit übrig, leer = abgelaufen)
    const fraction = state.totalSeconds > 0
      ? clamp(remaining / state.totalSeconds, 0, 1)
      : 0;
    el.progress.style.strokeDashoffset = String(CIRCUMFERENCE * (1 - fraction));

    // Sweepender Zeiger: eine Umdrehung pro Minute, im Uhrzeigersinn mit ablaufender Zeit
    const elapsed = state.totalSeconds - remaining;
    const angle = ((elapsed % 60) / 60) * 360;
    el.hand.style.transform = `rotate(${angle}deg)`;

    // Zustandsfarben
    document.body.classList.toggle("is-warn", !state.finished && remaining <= WARN_AT && remaining > DANGER_AT);
    document.body.classList.toggle("is-danger", !state.finished && remaining <= DANGER_AT && remaining > 0);
    document.body.classList.toggle("is-finished", state.finished);
  }

  // ---------- Lauf-Schleife ----------
  function loop() {
    const now = performance.now();
    state.remaining = Math.max(0, (state.endTime - now) / 1000);

    handleSoundCues();
    render();

    if (state.remaining <= 0) {
      finish();
      return;
    }
    state.rafId = requestAnimationFrame(loop);
  }

  function handleSoundCues() {
    const whole = Math.ceil(state.remaining);
    if (whole === state.lastPingSecond) return;
    state.lastPingSecond = whole;
    // Ping bei jedem 30-Sekunden-Schritt, aber nicht beim Start und nicht bei Null
    if (whole > 0 && whole < state.totalSeconds && whole % PING_INTERVAL === 0) {
      playPing();
    }
  }

  // ---------- Steuerung ----------
  function start() {
    if (state.running) return;
    if (state.remaining <= 0) state.remaining = state.totalSeconds;
    ensureAudio(); // im Nutzer-Gesten-Kontext freischalten
    state.finished = false;
    state.running = true;
    state.lastPingSecond = Math.ceil(state.remaining);
    state.endTime = performance.now() + state.remaining * 1000;
    el.startPause.textContent = "Pause";
    setStatus(`Läuft – noch ${formatTime(state.remaining)}`);
    setInputsDisabled(true);
    state.rafId = requestAnimationFrame(loop);
  }

  function pause() {
    if (!state.running) return;
    cancelAnimationFrame(state.rafId);
    state.running = false;
    el.startPause.textContent = "Weiter";
    setStatus(`Pausiert – noch ${formatTime(state.remaining)}`);
    setInputsDisabled(false);
  }

  function toggleStartPause() {
    state.running ? pause() : start();
  }

  function finish() {
    cancelAnimationFrame(state.rafId);
    state.running = false;
    state.finished = true;
    state.remaining = 0;
    el.startPause.textContent = "Start";
    render();
    setStatus("Zeit abgelaufen!");
    setInputsDisabled(false);
    playJingle();
  }

  function reset() {
    cancelAnimationFrame(state.rafId);
    state.running = false;
    state.finished = false;
    state.remaining = state.totalSeconds;
    state.lastPingSecond = null;
    el.startPause.textContent = "Start";
    setStatus(`Bereit – ${formatTime(state.totalSeconds)} eingestellt`);
    setInputsDisabled(false);
    render();
  }

  function setTotal(seconds, { quiet = false } = {}) {
    state.totalSeconds = clamp(Math.round(seconds), 1, 99 * 3600 + 59 * 60 + 59);
    syncInputs();
    reset();
    if (!quiet) setStatus(`Eingestellt: ${formatTime(state.totalSeconds)}`);
  }

  // ---------- UI-Helfer ----------
  function setStatus(text) { el.status.textContent = text; }

  function setInputsDisabled(disabled) {
    [el.inHours, el.inMinutes, el.inSeconds, el.applyTime, ...el.presets]
      .forEach((node) => { node.disabled = disabled; });
  }

  function syncInputs() {
    const s = state.totalSeconds;
    el.inHours.value = Math.floor(s / 3600);
    el.inMinutes.value = Math.floor((s % 3600) / 60);
    el.inSeconds.value = s % 60;
    markActivePreset();
  }

  function markActivePreset() {
    el.presets.forEach((btn) => {
      const active = Number(btn.dataset.seconds) === state.totalSeconds;
      btn.setAttribute("aria-current", active ? "true" : "false");
    });
  }

  function readInputs() {
    const h = clamp(parseInt(el.inHours.value, 10) || 0, 0, 99);
    const m = clamp(parseInt(el.inMinutes.value, 10) || 0, 0, 59);
    const s = clamp(parseInt(el.inSeconds.value, 10) || 0, 0, 59);
    return h * 3600 + m * 60 + s;
  }

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
  }

  function toggleMute() {
    state.muted = !state.muted;
    el.mute.setAttribute("aria-pressed", String(state.muted));
    el.mute.textContent = state.muted ? "🔇 Stumm" : "🔊 Ton";
  }

  // ---------- Events ----------
  function bindEvents() {
    el.startPause.addEventListener("click", toggleStartPause);
    el.reset.addEventListener("click", reset);
    el.fullscreen.addEventListener("click", toggleFullscreen);
    el.mute.addEventListener("click", toggleMute);

    el.applyTime.addEventListener("click", () => {
      const total = readInputs();
      if (total < 1) { setStatus("Bitte eine Zeit größer als 0 einstellen."); return; }
      setTotal(total);
    });

    el.presets.forEach((btn) => {
      btn.addEventListener("click", () => setTotal(Number(btn.dataset.seconds)));
    });

    document.addEventListener("fullscreenchange", () => {
      el.fullscreen.setAttribute("aria-pressed", String(!!document.fullscreenElement));
    });

    // Leertaste = Start/Pause (außer in Eingabefeldern)
    document.addEventListener("keydown", (e) => {
      if (e.code === "Space" && !["INPUT", "BUTTON"].includes(e.target.tagName)) {
        e.preventDefault();
        toggleStartPause();
      }
    });
  }

  // ---------- Init ----------
  function init() {
    buildTicks();
    bindEvents();
    syncInputs();
    render();
  }

  init();
})();
