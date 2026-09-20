window.PG = (function () {
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

  const patientName = (id) => (PATIENTS.find((p) => p.id === id) || {}).name || id;
  const levelInfo = (lvl) => LEVEL[(lvl || "info").toLowerCase()] || LEVEL.info;

  async function checkHealth(elId, txtId) {
    const el = document.getElementById(elId);
    const txt = document.getElementById(txtId);
    if (!el) return;
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

  function connectWs(onEvent) {
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    let base;
    if (API_BASE.startsWith("http")) {
      base = API_BASE.replace(/^http/, "ws").replace(/\/api\/v1\/?$/, "");
    } else {
      base = proto + "//" + location.host;
    }
    const url = `${base}${API_BASE.replace(/^https?:.*?(\/api)/, "$1")}/ws/alerts`;
    let ws, retry = 0;

    function open() {
      try {
        ws = new WebSocket(url);
      } catch (e) {
        return retryOpen();
      }
      ws.onopen = () => { retry = 0; };
      ws.onmessage = (ev) => {
        let m;
        try { m = JSON.parse(ev.data); } catch (e) { return; }
        onEvent(m);
      };
      ws.onclose = () => retryOpen();
      ws.onerror = () => { try { ws.close(); } catch (e) {} };
    }
    function retryOpen() {
      retry += 1;
      setTimeout(open, Math.min(1000 * Math.pow(1.6, retry), 15000));
    }
    open();
  }

  async function apiGet(path) {
    const r = await fetch(API_BASE + path, { cache: "no-store" });
    return r.json();
  }

  function setActiveNav() {
    const path = location.pathname.replace(/\/$/, "") || "/";
    document.querySelectorAll(".nav a").forEach((a) => {
      const href = a.getAttribute("href").replace(/\/$/, "") || "/";
      if (href === path) a.classList.add("active");
    });
  }

  function toast(data) {
    let el = document.getElementById("toast");
    if (!el) {
      el = document.createElement("div");
      el.id = "toast";
      el.className = "toast";
      document.body.appendChild(el);
    }
    const lvl = (data.alert && data.alert.level) || "info";
    el.className = "toast " + lvl;
    el.innerHTML = `<strong>${esc(levelInfo(lvl).label)} · ${esc(data.patient_name || "")}</strong>
      ${esc(data.admission_reason || "")}`;
    requestAnimationFrame(() => el.classList.add("show"));
    clearTimeout(el._t);
    el._t = setTimeout(() => el.classList.remove("show"), 6000);
  }

  document.addEventListener("DOMContentLoaded", setActiveNav);

  return { API_BASE, PATIENTS, LEVEL, esc, fmtTime, patientName, levelInfo, checkHealth, connectWs, apiGet, toast };
})();
