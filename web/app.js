(function () {
  "use strict";

  const params = new URLSearchParams(location.search);
  const API_BASE =
    params.get("api") ||
    window.PULSEGUARD_API_BASE ||
    "/api/v1";

  const PATIENTS = [
    { id: "PAT-001", name: "Juan García", policy: "POL-2024-001" },
    { id: "PAT-002", name: "María López", policy: "POL-2024-002" },
    { id: "PAT-003", name: "Pedro Martínez", policy: "POL-2024-003" },
    { id: "PAT-004", name: "Ana Rodríguez", policy: "POL-2024-004" },
    { id: "PAT-005", name: "Carlos Mendoza", policy: "POL-2024-005" },
    { id: "PAT-006", name: "Laura Fernández", policy: "POL-2024-006" },
    { id: "PAT-007", name: "Roberto Díaz", policy: "POL-2024-007" },
    { id: "PAT-008", name: "Isabel Torres", policy: "POL-2024-008" },
  ];

  const $ = (id) => document.getElementById(id);
  const esc = (s) =>
    String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );
  const fmtDate = (iso) => {
    if (!iso) return "–";
    const d = new Date(iso);
    return isNaN(d) ? esc(iso) : d.toLocaleString("es-PA", { hour12: false });
  };

  /* ---------- selects ---------- */
  function initSelects() {
    const pSel = $("patientSelect");
    const polSel = $("policySelect");
    pSel.innerHTML = PATIENTS.map(
      (p) => `<option value="${p.id}">${esc(p.name)} (${p.id})</option>`
    ).join("");
    polSel.innerHTML = PATIENTS.map(
      (p) => `<option value="${p.policy}">${p.policy}</option>`
    ).join("");
    pSel.addEventListener("change", () => {
      const found = PATIENTS.find((p) => p.id === pSel.value);
      if (found) polSel.value = found.policy;
    });

    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    $("timestamp").value = now.toISOString().slice(0, 16);
  }

  /* ---------- API status ---------- */
  async function checkHealth() {
    const el = $("apiStatus");
    const txt = $("apiStatusText");
    try {
      const r = await fetch("/health", { cache: "no-store" });
      const d = await r.json();
      const ok = r.ok && d.database === "connected";
      el.className = "status " + (ok ? "ok" : "bad");
      txt.textContent = ok ? "API + DB conectadas" : "API degradada";
    } catch (e) {
      el.className = "status bad";
      txt.textContent = "API no disponible";
    }
  }

  /* ---------- form ---------- */
  async function submitAdmission(ev) {
    ev.preventDefault();
    const btn = $("submitBtn");
    btn.disabled = true;
    btn.textContent = "Procesando…";

    const hr = $("hr").value, bp = $("bp").value, spo2 = $("spo2").value;
    const vitals = {};
    if (hr) vitals.heart_rate = Number(hr);
    if (bp) vitals.blood_pressure = bp;
    if (spo2) vitals.oxygen_saturation = Number(spo2);

    const payload = {
      admission_id: "ADM-" + Date.now(),
      patient_id: $("patientSelect").value,
      policy_number: $("policySelect").value,
      timestamp: new Date($("timestamp").value || Date.now()).toISOString(),
      admission_reason: $("reason").value.trim(),
      symptoms: $("symptoms").value.split(",").map((s) => s.trim()).filter(Boolean),
      hospital_code: $("hospital").value,
    };
    if (Object.keys(vitals).length) payload.vital_signs = vitals;

    try {
      const r = await fetch(`${API_BASE}/webhook/admission`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail ? JSON.stringify(data.detail) : r.statusText);
      renderResult(data, payload);
      loadAll();
    } catch (e) {
      renderError(e.message || "Error al procesar la admisión");
    } finally {
      btn.disabled = false;
      btn.textContent = "Procesar Admisión";
    }
  }

  /* ---------- result rendering ---------- */
  function renderError(msg) {
    $("resultBody").innerHTML =
      `<div class="alert-banner critical"><span class="badge">Error</span>
       <div>${esc(msg)}</div></div>`;
  }

  function renderResult(d, req) {
    const lvl = (d.alert_level || "info").toLowerCase();
    $("resultTime").textContent = fmtDate(new Date().toISOString());
    const chips = `
      <div class="chips">
        <span class="chip ${d.hospital_notified ? "on" : "off"}">
          ${d.hospital_notified ? "✓" : "✕"} Hospital notificado</span>
        <span class="chip ${d.insurer_notified ? "on" : "off"}">
          ${d.insurer_notified ? "✓" : "✕"} Gestor de casos notificado</span>
      </div>`;
    const recos = (d.recommendations || []).length
      ? `<ul class="reco">${d.recommendations.map((r) => `<li>${esc(r)}</li>`).join("")}</ul>`
      : "";
    const ai = d.ai_report
      ? `<div class="ai-report">${esc(d.ai_report)}</div>`
      : "";
    $("resultBody").innerHTML = `
      <div class="alert-banner ${lvl}">
        <span class="badge">${esc(lvl)}</span>
        <strong>${esc(d.message || "")}</strong>
      </div>
      <div class="result-grid">
        <div class="kv"><span>Admisión</span><span>${esc(d.admission_id)}</span></div>
        <div class="kv"><span>Paciente</span><span>${esc(req.patient_id)}</span></div>
        <div class="kv"><span>Póliza</span><span>${esc(req.policy_number)}</span></div>
        <div class="kv"><span>Motivo</span><span>${esc(req.admission_reason)}</span></div>
        <div class="kv"><span>Hospital</span><span>${esc(req.hospital_code)}</span></div>
      </div>
      ${chips}
      ${recos}
      ${ai}`;
  }

  /* ---------- KPIs + tables ---------- */
  function setKpi(id, v) { $(id).textContent = v == null ? "0" : v; }

  function applyStats(s) {
    if (!s) return;
    setKpi("kpiTotal", s.total_admissions);
    setKpi("kpiToday", s.admissions_today ?? s.today_admissions);
    const by = s.alerts_by_level || {};
    setKpi("kpiInfo", by.info || 0);
    setKpi("kpiWarning", by.warning || 0);
    setKpi("kpiCritical", by.critical || 0);
  }

  async function loadStats() {
    try {
      const r = await fetch(`${API_BASE}/alerts/stats`, { cache: "no-store" });
      applyStats(await r.json());
    } catch (e) { /* ignore */ }
  }

  async function loadAdmissions() {
    try {
      const r = await fetch(`${API_BASE}/admissions?limit=20`, { cache: "no-store" });
      const d = await r.json();
      const rows = (d.admissions || []).map(
        (a) => `<tr>
          <td>${esc(a.admission_id)}</td>
          <td>${esc(a.patient_id)}</td>
          <td>${esc(a.policy_number)}</td>
          <td>${esc(a.admission_reason)}</td>
          <td>${esc(a.hospital_code)}</td>
          <td><span class="pill ok">${esc(a.status)}</span></td>
        </tr>`
      );
      $("admissionsBody").innerHTML =
        rows.join("") || `<tr><td colspan="6" class="empty">Sin datos</td></tr>`;
    } catch (e) { /* ignore */ }
  }

  async function loadAlerts() {
    try {
      const level = $("levelFilter").value;
      const q = level ? `?level=${encodeURIComponent(level)}&limit=20` : "?limit=20";
      const r = await fetch(`${API_BASE}/alerts${q}`, { cache: "no-store" });
      const d = await r.json();
      const rows = (d.alerts || []).map(
        (a) => `<tr>
          <td><span class="pill ${esc(a.level)}">${esc(a.level)}</span></td>
          <td>${esc(a.admission_id)}</td>
          <td>${esc(a.message)}</td>
          <td><span class="pill ${a.hospital_notified ? "ok" : "no"}">${a.hospital_notified ? "sí" : "no"}</span></td>
          <td><span class="pill ${a.insurer_notified ? "ok" : "no"}">${a.insurer_notified ? "sí" : "no"}</span></td>
          <td>${fmtDate(a.created_at)}</td>
        </tr>`
      );
      $("alertsBody").innerHTML =
        rows.join("") || `<tr><td colspan="6" class="empty">Sin datos</td></tr>`;
    } catch (e) { /* ignore */ }
  }

  function loadAll() {
    loadStats();
    loadAdmissions();
    loadAlerts();
  }

  /* ---------- toast ---------- */
  let toastTimer;
  function toast(data) {
    const el = $("toast");
    const lvl = (data.alert && data.alert.level) || "info";
    el.className = "toast " + lvl;
    el.innerHTML = `<strong>${esc(lvl.toUpperCase())} · ${esc(data.patient_name)}</strong>
      ${esc(data.admission_reason)} — ${esc((data.alert && data.alert.message) || "")}`;
    requestAnimationFrame(() => el.classList.add("show"));
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove("show"), 6000);
  }

  /* ---------- websocket (tiempo real) ---------- */
  let ws, retry = 0;
  function connectWs() {
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    let base;
    if (API_BASE.startsWith("http")) {
      base = API_BASE.replace(/^http/, "ws").replace(/\/api\/v1\/?$/, "");
    } else {
      base = proto + "//" + location.host;
    }
    const url = `${base}${API_BASE.replace(/^https?:.*?(\/api)/, "$1")}/ws/alerts`;
    try {
      ws = new WebSocket(url);
    } catch (e) {
      return scheduleReconnect();
    }

    ws.onopen = () => { retry = 0; };
    ws.onmessage = (ev) => {
      let msg;
      try { msg = JSON.parse(ev.data); } catch (e) { return; }
      if (msg.event === "admission.processed") {
        renderResult(msg.data, {
          patient_id: msg.data.patient_id,
          policy_number: msg.data.policy_number,
          admission_reason: msg.data.admission_reason,
          hospital_code: msg.data.hospital_code,
        });
        applyStats(msg.data.stats);
        loadAdmissions();
        loadAlerts();
        toast(msg.data);
      }
    };
    ws.onclose = () => scheduleReconnect();
    ws.onerror = () => { try { ws.close(); } catch (e) {} };
  }

  function scheduleReconnect() {
    retry += 1;
    const delay = Math.min(1000 * Math.pow(1.6, retry), 15000);
    setTimeout(connectWs, delay);
  }

  /* ---------- init ---------- */
  document.addEventListener("DOMContentLoaded", () => {
    initSelects();
    $("admissionForm").addEventListener("submit", submitAdmission);
    $("refreshBtn").addEventListener("click", loadAll);
    $("levelFilter").addEventListener("change", loadAlerts);

    const toastEl = document.createElement("div");
    toastEl.id = "toast";
    toastEl.className = "toast";
    document.body.appendChild(toastEl);

    checkHealth();
    loadAll();
    connectWs();

    setInterval(checkHealth, 20000);
    setInterval(loadStats, 15000);
  });
})();
