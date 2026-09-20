(function () {
  "use strict";
  const { esc, fmtTime, patientName, levelInfo, checkHealth, connectWs, apiGet, toast, initNotify, notify } = window.PG;

  const admissionPatient = {};
  const admissionReason = {};
  const rendered = new Set();

  const $ = (id) => document.getElementById(id);

  function hero() {
    $("heroDate").textContent = new Date().toLocaleDateString("es-PA", {
      weekday: "long", day: "numeric", month: "long",
    });
  }

  function card(n) {
    const lvl = (n.level || "info").toLowerCase();
    const recos = (n.recommendations || []).length
      ? `<ul class="reco">${n.recommendations.map((r) => `<li>${esc(r)}</li>`).join("")}</ul>`
      : "";
    const name = n.patient_name || patientName(admissionPatient[n.admission_id] || "");
    return `<article class="notif ${lvl}" data-id="${esc(n.admission_id)}">
      <div class="notif__top">
        <span class="pill ${lvl}">${esc(levelInfo(lvl).label)}</span>
        <span class="notif__time">${fmtTime(n.created_at || new Date().toISOString())}</span>
      </div>
      <div class="notif__body">
        <div class="kv"><span>Paciente</span><span>${esc(name)}</span></div>
        <div class="kv"><span>Motivo</span><span>${esc(n.admission_reason || admissionReason[n.admission_id] || "–")}</span></div>
        <div class="kv"><span>Cobertura</span><span>${esc(n.message || "")}</span></div>
        ${recos}
      </div>
    </article>`;
  }

  function addNotif(n, prepend) {
    if (!n.admission_id || rendered.has(n.admission_id)) return;
    rendered.add(n.admission_id);
    const feed = $("feed");
    const empty = feed.querySelector(".empty");
    if (empty) empty.remove();
    const html = card(n);
    if (prepend) feed.insertAdjacentHTML("afterbegin", html);
    else feed.insertAdjacentHTML("beforeend", html);
  }

  async function loadStats() {
    try {
      const s = await apiGet("/alerts/stats");
      const by = s.alerts_by_level || {};
      $("kpiTotal").textContent = s.total_alerts || 0;
      $("kpiInfo").textContent = by.info || 0;
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
      const list = (d.alerts || []).slice().reverse();
      list.forEach((a) => addNotif({
        admission_id: a.admission_id,
        level: a.level,
        message: a.message,
        recommendations: a.recommendations,
        created_at: a.created_at,
      }, false));
    } catch (e) {}
    loadStats();
  }

  document.addEventListener("DOMContentLoaded", () => {
    hero();
    initNotify("notifyBtn");
    checkHealth("apiStatus", "apiStatusText");
    loadHistory();
    $("refreshBtn").addEventListener("click", () => {
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
        recommendations: d.alert && d.alert.recommendations,
      }, true);
      loadStats();
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
