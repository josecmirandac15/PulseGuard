(function () {
  "use strict";

  const params = new URLSearchParams(location.search);
  const API_BASE = params.get("api") || window.PULSEGUARD_API_BASE || "/api/v1";

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

  const LEVEL = {
    info: { label: "Sin observaciones", short: "Normal" },
    warning: { label: "Requiere revisión", short: "Revisión" },
    critical: { label: "Atención inmediata", short: "Crítico" },
  };

  const patientName = (id) => (PATIENTS.find((p) => p.id === id) || {}).name || id;
  const admissionPatient = {}; // admission_id -> patient_id

  const $ = (id) => document.getElementById(id);
  const esc = (s) =>
    String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );
  const fmtTime = (iso) => {
    if (!iso) return "–";
    const d = new Date(iso);
    return isNaN(d)
      ? esc(iso)
      : d.toLocaleString("es-PA", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
  };

  /* ---------- hero ---------- */
  function initHero() {
    const h = new Date().getHours();
    $("greeting").textContent =
      h < 12 ? "Buenos días" : h < 19 ? "Buenas tardes" : "Buenas noches";
    $("heroDate").textContent = new Date().toLocaleDateString("es-PA", {
      weekday: "long", day: "numeric", month: "long",
    });
  }

  /* ---------- selects ---------- */
  function initSelects() {
    const pSel = $("patientSelect");
    const polSel = $("policySelect");
    pSel.innerHTML = PATIENTS.map(
      (p) => `<option value="${p.id}">${esc(p.name)}</option>`
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

  /* ---------- status ---------- */
  async function checkHealth() {
    const el = $("apiStatus");
    const txt = $("apiStatusText");
    try {
      const r = await fetch("/health", { cache: "no-store" });
      const d = await r.json();
      const ok = r.ok && d.database === "connected";
      el.className = "status " + (ok ? "ok" : "bad");
      txt.textContent = ok ? "Sistema en línea" : "Servicio inestable";
    } catch (e) {
      el.className = "status bad";
      txt.textContent = "Sin conexión";
    }
  }

  /* ---------- form ---------- */
  async function submitAdmission(ev) {
    ev.preventDefault();
    const btn = $("submitBtn");
    btn.disabled = true;
    btn.textContent = "Evaluando…";

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
      if (!r.ok) throw new Error("No se pudo registrar el ingreso.");
      admissionPatient[data.admission_id] = payload.patient_id;
      renderResult(data, payload);
      loadAll();
    } catch (e) {
      renderError(e.message || "No se pudo registrar el ingreso.");
    } finally {
      btn.disabled = false;
      btn.textContent = "Evaluar y notificar";
    }
  }

  /* ---------- result ---------- */
  function renderError(msg) {
    $("resultBody").innerHTML =
      `<div class="alert-banner critical"><span class="badge">Error</span>
       <strong>${esc(msg)}</strong></div>`;
  }

  function renderResult(d, req) {
    const lvl = (d.alert_level || "info").toLowerCase();
    const info = LEVEL[lvl] || LEVEL.info;
    $("resultTime").textContent = fmtTime(new Date().toISOString());

    const chips = `
      <div class="chips">
        <span class="chip ${d.hospital_notified ? "on" : "off"}">
          ${d.hospital_notified ? "✓" : "✕"} Admisiones del hospital</span>
        <span class="chip ${d.insurer_notified ? "on" : "off"}">
          ${d.insurer_notified ? "✓" : "✕"} Gestor de casos del seguro</span>
      </div>`;
    const recos = (d.recommendations || []).length
      ? `<ul class="reco">${d.recommendations.map((r) => `<li>${esc(r)}</li>`).join("")}</ul>`
      : "";
    const report = d.ai_report
      ? `<div class="report">${esc(d.ai_report)}</div>`
      : "";

    $("resultBody").innerHTML = `
      <div class="alert-banner ${lvl}">
        <span class="badge">${esc(info.label)}</span>
        <strong>${esc(d.message || "")}</strong>
      </div>
      <div class="kv-list">
        <div class="kv"><span>Paciente</span><span>${esc(patientName(req.patient_id))}</span></div>
        <div class="kv"><span>Póliza</span><span>${esc(req.policy_number)}</span></div>
        <div class="kv"><span>Motivo</span><span>${esc(req.admission_reason)}</span></div>
        <div class="kv"><span>Hospital</span><span>${esc(req.hospital_code)}</span></div>
      </div>
      ${chips}
      ${recos}
      ${report}`;
  }

  /* ---------- kpis + tables ---------- */
  const setKpi = (id, v) => ($(id).textContent = v == null ? "0" : v);

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
    } catch (e) { /* silencioso */ }
  }

  async function loadAdmissions() {
    try {
      const r = await fetch(`${API_BASE}/admissions?limit=20`, { cache: "no-store" });
      const d = await r.json();
      (d.admissions || []).forEach((a) => (admissionPatient[a.admission_id] = a.patient_id));
      const rows = (d.admissions || []).map(
        (a) => `<tr>
          <td>${esc(a.admission_id)}</td>
          <td>${esc(patientName(a.patient_id))}</td>
          <td>${esc(a.policy_number)}</td>
          <td>${esc(a.admission_reason)}</td>
          <td>${esc(a.hospital_code)}</td>
        </tr>`
      );
      $("admissionsBody").innerHTML =
        rows.join("") || `<tr><td colspan="5" class="empty">Sin registros</td></tr>`;
    } catch (e) { /* silencioso */ }
  }

  async function loadAlerts() {
    try {
      const level = $("levelFilter").value;
      const q = level ? `?level=${encodeURIComponent(level)}&limit=20` : "?limit=20";
      const r = await fetch(`${API_BASE}/alerts${q}`, { cache: "no-store" });
      const d = await r.json();
      const rows = (d.alerts || []).map((a) => {
        const lvl = (a.level || "info").toLowerCase();
        const pid = admissionPatient[a.admission_id];
        return `<tr>
          <td><span class="pill ${lvl}">${esc((LEVEL[lvl] || LEVEL.info).short)}</span></td>
          <td>${esc(pid ? patientName(pid) : a.admission_id)}</td>
          <td><span class="pill ${a.hospital_notified ? "ok" : "no"}">${a.hospital_notified ? "Enviada" : "Pendiente"}</span></td>
          <td><span class="pill ${a.insurer_notified ? "ok" : "no"}">${a.insurer_notified ? "Enviada" : "Pendiente"}</span></td>
          <td>${fmtTime(a.created_at)}</td>
        </tr>`;
      });
      $("alertsBody").innerHTML =
        rows.join("") || `<tr><td colspan="5" class="empty">Sin registros</td></tr>`;
    } catch (e) { /* silencioso */ }
  }

  async function loadAll() {
    loadStats();
    await loadAdmissions();
    loadAlerts();
  }

  /* ---------- toast ---------- */
  let toastTimer;
  function toast(data) {
    const el = $("toast");
    const lvl = (data.alert && data.alert.level) || "info";
    el.className = "toast " + lvl;
    el.innerHTML = `<strong>${esc((LEVEL[lvl] || LEVEL.info).label)} · ${esc(data.patient_name || "")}</strong>
      ${esc(data.admission_reason || "")} — ${esc((data.alert && data.alert.message) || "")}`;
    requestAnimationFrame(() => el.classList.add("show"));
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove("show"), 6000);
  }

  /* ---------- tiempo real ---------- */
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
        const d = msg.data;
        admissionPatient[d.admission_id] = d.patient_id;
        renderResult(d, {
          patient_id: d.patient_id,
          policy_number: d.policy_number,
          admission_reason: d.admission_reason,
          hospital_code: d.hospital_code,
        });
        applyStats(d.stats);
        loadAdmissions().then(loadAlerts);
        toast(d);
      }
    };
    ws.onclose = () => scheduleReconnect();
    ws.onerror = () => { try { ws.close(); } catch (e) {} };
  }
  function scheduleReconnect() {
    retry += 1;
    setTimeout(connectWs, Math.min(1000 * Math.pow(1.6, retry), 15000));
  }

  /* ---------- init ---------- */
  document.addEventListener("DOMContentLoaded", () => {
    initHero();
    initSelects();
    $("admissionForm").addEventListener("submit", submitAdmission);
    $("refreshBtn").addEventListener("click", loadAll);
    $("levelFilter").addEventListener("change", loadAlerts);

    const t = document.createElement("div");
    t.id = "toast";
    t.className = "toast";
    document.body.appendChild(t);

    checkHealth();
    loadAll();
    connectWs();
    setInterval(checkHealth, 20000);
    setInterval(loadStats, 15000);
  });
})();
