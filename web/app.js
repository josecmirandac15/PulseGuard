(function () {
  "use strict";
  const { API_BASE, PATIENTS, esc, fmtTime, patientName, levelInfo, checkHealth, connectWs, apiGet, toast, initNotify, notify } = window.PG;

  const admissionPatient = {};

  const $ = (id) => document.getElementById(id);
  const setKpi = (id, v) => ($(id).textContent = v == null ? "0" : v);

  function initHero() {
    const h = new Date().getHours();
    $("greeting").textContent = h < 12 ? "Buenos días" : h < 19 ? "Buenas tardes" : "Buenas noches";
    $("heroDate").textContent = new Date().toLocaleDateString("es-PA", {
      weekday: "long", day: "numeric", month: "long",
    });
  }

  const byName = {};
  const byPolicy = {};
  PATIENTS.forEach((p) => { byName[p.name.toLowerCase()] = p; byPolicy[p.policy] = p; });

  function initInputs() {
    const pIn = $("patientInput");
    const polIn = $("policyInput");
    $("patientsList").innerHTML = PATIENTS.map((p) => `<option value="${esc(p.name)}"></option>`).join("");
    $("policiesList").innerHTML = PATIENTS.map((p) => `<option value="${p.policy}"></option>`).join("");

    pIn.addEventListener("input", () => {
      const p = byName[pIn.value.trim().toLowerCase()];
      if (p) {
        $("patientHint").textContent = "ID: " + p.id + " · póliza " + p.policy;
        polIn.value = p.policy;
      } else {
        $("patientHint").textContent = pIn.value.trim() ? "Paciente nuevo (no registrado)" : "";
      }
    });

    polIn.addEventListener("input", () => {
      const p = byPolicy[polIn.value.trim()];
      if (p) {
        pIn.value = p.name;
        $("patientHint").textContent = "ID: " + p.id + " · póliza " + p.policy;
      }
    });

    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    $("timestamp").value = now.toISOString().slice(0, 16);

    pIn.value = PATIENTS[0].name;
    polIn.value = PATIENTS[0].policy;
    $("patientHint").textContent = "ID: " + PATIENTS[0].id + " · póliza " + PATIENTS[0].policy;
  }

  async function submitAdmission(ev) {
    ev.preventDefault();

    const typedName = $("patientInput").value.trim();
    const typedPolicy = $("policyInput").value.trim();
    if (!typedName || !typedPolicy) {
      $("resultBody").innerHTML =
        `<div class="alert-banner critical"><span class="badge">Falta</span>
         <strong>Indica el nombre del paciente y la póliza.</strong></div>`;
      return;
    }

    const btn = $("submitBtn");
    btn.disabled = true;
    btn.textContent = "Evaluando…";

    const hr = $("hr").value, bp = $("bp").value, spo2 = $("spo2").value;
    const vitals = {};
    if (hr) vitals.heart_rate = Number(hr);
    if (bp) vitals.blood_pressure = bp;
    if (spo2) vitals.oxygen_saturation = Number(spo2);

    const matched = byName[typedName.toLowerCase()];
    const payload = {
      admission_id: "ADM-" + Date.now(),
      patient_id: matched ? matched.id : typedName,
      policy_number: typedPolicy,
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
      $("resultBody").innerHTML =
        `<div class="alert-banner critical"><span class="badge">Error</span>
         <strong>${esc(e.message || "No se pudo registrar el ingreso.")}</strong></div>`;
    } finally {
      btn.disabled = false;
      btn.textContent = "Evaluar y notificar";
    }
  }

  function renderResult(d, req) {
    const lvl = (d.alert_level || "info").toLowerCase();
    $("resultTime").textContent = fmtTime(new Date().toISOString());
    const chips = `
      <div class="chips">
        <span class="chip ${d.hospital_notified ? "on" : "off"}">${d.hospital_notified ? "✓" : "✕"} Admisiones del hospital</span>
        <span class="chip ${d.insurer_notified ? "on" : "off"}">${d.insurer_notified ? "✓" : "✕"} Gestor de casos del seguro</span>
      </div>`;
    const recos = (d.recommendations || []).length
      ? `<ul class="reco">${d.recommendations.map((r) => `<li>${esc(r)}</li>`).join("")}</ul>`
      : "";
    const report = d.ai_report ? `<div class="report">${esc(d.ai_report)}</div>` : "";
    $("resultBody").innerHTML = `
      <div class="alert-banner ${lvl}">
        <span class="badge">${esc(levelInfo(lvl).label)}</span>
        <strong>${esc(d.message || "")}</strong>
      </div>
      <div class="kv-list">
        <div class="kv"><span>Paciente</span><span>${esc(patientName(req.patient_id))}</span></div>
        <div class="kv"><span>Póliza</span><span>${esc(req.policy_number)}</span></div>
        <div class="kv"><span>Motivo</span><span>${esc(req.admission_reason)}</span></div>
        <div class="kv"><span>Hospital</span><span>${esc(req.hospital_code)}</span></div>
      </div>${chips}${recos}${report}`;
  }

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
    try { applyStats(await apiGet("/alerts/stats")); } catch (e) {}
  }

  async function loadAdmissions() {
    try {
      const d = await apiGet("/admissions?limit=20");
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
      $("admissionsBody").innerHTML = rows.join("") || `<tr><td colspan="5" class="empty">Sin registros</td></tr>`;
    } catch (e) {}
  }

  async function loadAlerts() {
    try {
      const level = $("levelFilter").value;
      const q = level ? `?level=${encodeURIComponent(level)}&limit=20` : "?limit=20";
      const d = await apiGet("/alerts" + q);
      const rows = (d.alerts || []).map((a) => {
        const lvl = (a.level || "info").toLowerCase();
        const pid = admissionPatient[a.admission_id];
        return `<tr>
          <td><span class="pill ${lvl}">${esc(levelInfo(lvl).short)}</span></td>
          <td>${esc(pid ? patientName(pid) : a.admission_id)}</td>
          <td>${esc(a.message)}</td>
          <td>${fmtTime(a.created_at)}</td>
        </tr>`;
      });
      $("alertsBody").innerHTML = rows.join("") || `<tr><td colspan="4" class="empty">Sin registros</td></tr>`;
    } catch (e) {}
  }

  async function loadAll() {
    loadStats();
    await loadAdmissions();
    loadAlerts();
  }

  document.addEventListener("DOMContentLoaded", () => {
    initHero();
    initInputs();
    initNotify("notifyBtn");
    $("admissionForm").addEventListener("submit", submitAdmission);
    $("refreshBtn").addEventListener("click", loadAll);
    $("levelFilter").addEventListener("change", loadAlerts);

    checkHealth("apiStatus", "apiStatusText");
    loadAll();

    connectWs((msg) => {
      if (msg.event !== "admission.processed") return;
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
      const lvl = (d.alert && d.alert.level) || "info";
      notify(
        "Nuevo ingreso · " + levelInfo(lvl).label,
        (d.patient_name || "Paciente") + " — " + (d.admission_reason || ""),
        d.admission_id
      );
    });

    setInterval(() => checkHealth("apiStatus", "apiStatusText"), 20000);
    setInterval(loadStats, 15000);
  });
})();
