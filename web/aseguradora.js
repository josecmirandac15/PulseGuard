(function () {
  "use strict";
  const { esc, fmtTime, patientName, levelInfo, checkHealth, connectWs, apiGet, toast } = window.PG;

  const admissionPatient = {};
  const admissionReason = {};
  const rendered = new Map(); // admission_id -> level

  const $ = (id) => document.getElementById(id);

  function hero() {
    $("heroDate").textContent = new Date().toLocaleDateString("es-PA", {
      weekday: "long", day: "numeric", month: "long",
    });
  }

  function card(n) {
    const lvl = (n.level || "info").toLowerCase();
    const name = n.patient_name || patientName(admissionPatient[n.admission_id] || "");
    const analysis = n.agent_analysis
      ? `<div class="kv"><span>Análisis</span><span>${esc(n.agent_analysis)}</span></div>`
      : "";
    const report = n.ai_report
      ? `<details class="report-toggle"><summary>Informe del caso</summary><div class="report">${esc(n.ai_report)}</div></details>`
      : "";
    return `<article class="notif ${lvl}" data-id="${esc(n.admission_id)}" data-level="${lvl}">
      <div class="notif__top">
        <span class="pill ${lvl}">${esc(levelInfo(lvl).label)}</span>
        <span class="notif__time">${fmtTime(n.created_at || new Date().toISOString())}</span>
      </div>
      <div class="notif__body">
        <div class="kv"><span>Paciente</span><span>${esc(name)}</span></div>
        <div class="kv"><span>Motivo</span><span>${esc(n.admission_reason || admissionReason[n.admission_id] || "–")}</span></div>
        <div class="kv"><span>Evaluación</span><span>${esc(n.message || "")}</span></div>
        ${analysis}
        ${report}
      </div>
    </article>`;
  }

  function visible(level) {
    if (!$("onlyReview").checked) return true;
    return level === "warning" || level === "critical";
  }

  function addNotif(n, prepend) {
    if (!n.admission_id) return;
    if (rendered.has(n.admission_id)) {
      const el = document.querySelector(`.notif[data-id="${CSS.escape(n.admission_id)}"]`);
      if (el) el.remove();
    }
    rendered.set(n.admission_id, n.level);
    if (!visible((n.level || "info").toLowerCase())) return;
    const feed = $("feed");
    const empty = feed.querySelector(".empty");
    if (empty) empty.remove();
    const html = card(n);
    if (prepend) feed.insertAdjacentHTML("afterbegin", html);
    else feed.insertAdjacentHTML("beforeend", html);
  }

  function applyFilter() {
    document.querySelectorAll("#feed .notif").forEach((el) => {
      el.style.display = visible(el.dataset.level) ? "" : "none";
    });
  }

  async function loadStats() {
    try {
      const s = await apiGet("/alerts/stats");
      const by = s.alerts_by_level || {};
      $("kpiTotal").textContent = s.total_alerts || 0;
      $("kpiWarning").textContent = by.warning || 0;
      $("kpiCritical").textContent = by.critical || 0;
    } catch (e) {}
  }

  async function loadHistory() {
    try {
      const adm = await apiGet("/admissions?limit=50");
      (adm.admissions || []).forEach((a) => {
        admissionPatient[a.admission_id] = a.patient_id;
        admissionReason[a.admission_id] = a.admission_reason;
      });
    } catch (e) {}
    try {
      const d = await apiGet("/alerts?limit=30");
      (d.alerts || []).slice().reverse().forEach((a) => addNotif({
        admission_id: a.admission_id,
        level: a.level,
        message: a.message,
        agent_analysis: a.agent_analysis,
        ai_report: a.ai_report,
        created_at: a.created_at,
      }, false));
    } catch (e) {}
    applyFilter();
    loadStats();
  }

  document.addEventListener("DOMContentLoaded", () => {
    hero();
    checkHealth("apiStatus", "apiStatusText");
    loadHistory();
    $("onlyReview").addEventListener("change", applyFilter);
    $("refreshBtn") && $("refreshBtn").addEventListener("click", () => {
      rendered.clear();
      $("feed").innerHTML = "";
      loadHistory();
    });

    connectWs((msg) => {
      if (msg.event !== "admission.processed") return;
      const d = msg.data;
      admissionPatient[d.admission_id] = d.patient_id;
      addNotif({
        admission_id: d.admission_id,
        patient_name: d.patient_name,
        admission_reason: d.admission_reason,
        level: d.alert && d.alert.level,
        message: d.alert && d.alert.message,
        ai_report: d.alert && d.alert.ai_report,
      }, true);
      loadStats();
      toast(d);
    });

    setInterval(() => checkHealth("apiStatus", "apiStatusText"), 20000);
    setInterval(loadStats, 15000);
  });
})();
