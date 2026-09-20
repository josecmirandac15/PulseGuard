window.PG = (function () {
  "use strict";

  const params = new URLSearchParams(location.search);
  const API_BASE = params.get("api") || window.PULSEGUARD_API_BASE || "/api/v1";

  const PATIENTS = [
    { id: "PAT-001", name: "Juan García", policy: "HG-2026-0001" },
    { id: "PAT-002", name: "María López", policy: "HG-2026-0002" },
    { id: "PAT-003", name: "Pedro Martínez", policy: "HG-2026-0003" },
    { id: "PAT-004", name: "Ana Rodríguez", policy: "HG-2026-0004" },
    { id: "PAT-005", name: "Carlos Mendoza", policy: "HG-2026-0005" },
    { id: "PAT-006", name: "Laura Fernández", policy: "HG-2026-0006" },
    { id: "PAT-007", name: "Roberto Díaz", policy: "HG-2026-0007" },
    { id: "PAT-008", name: "Isabel Torres", policy: "HG-2026-0008" },
    { id: "PAT-009", name: "Ricardo Aparicio", policy: "HG-2026-0009" },
    { id: "PAT-010", name: "Yolanda Quintero", policy: "HG-2026-0010" },
    { id: "PAT-011", name: "Andrés Bethancourt", policy: "HG-2026-0011" },
    { id: "PAT-012", name: "Carmen Espinosa", policy: "HG-2026-0012" },
    { id: "PAT-013", name: "Gabriel Iturralde", policy: "HG-2026-0013" },
    { id: "PAT-014", name: "Sofía Vallarino", policy: "HG-2026-0014" },
  ];
  let _patients = PATIENTS;

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

  const patientName = (id) => (_patients.find((p) => p.id === id) || {}).name || id;
  const levelInfo = (lvl) => LEVEL[(lvl || "info").toLowerCase()] || LEVEL.info;

  async function loadPatients() {
    try {
      const d = await apiGet("/patients");
      if (d && Array.isArray(d.patients) && d.patients.length) {
        _patients = d.patients.map((p) => ({
          id: p.patient_id,
          name: p.name,
          policy: p.policy_number || "",
        }));
      }
    } catch (e) { /* usa el respaldo */ }
    return _patients;
  }

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

  /* ---------- notificaciones del navegador ---------- */
  const NOTIFY_KEY = "pg_notify_enabled";
  const notifySupported = () => "Notification" in window;
  const notifyEnabled = () =>
    notifySupported() &&
    Notification.permission === "granted" &&
    localStorage.getItem(NOTIFY_KEY) === "1";

  function renderBell(btn) {
    const label = btn.querySelector("span");
    if (!notifySupported()) { btn.style.display = "none"; return; }
    if (Notification.permission === "denied") {
      btn.classList.remove("on");
      btn.title = "Notificaciones bloqueadas en el navegador";
      if (label) label.textContent = "Notificaciones bloqueadas";
    } else if (notifyEnabled()) {
      btn.classList.add("on");
      btn.title = "Alertas activadas (clic para desactivar)";
      if (label) label.textContent = "Alertas activadas";
    } else {
      btn.classList.remove("on");
      btn.title = "Activar avisos de nuevos ingresos";
      if (label) label.textContent = "Activar alertas";
    }
  }

  function initNotify(btnId) {
    const btn = document.getElementById(btnId);
    if (!btn) return;
    renderBell(btn);
    btn.addEventListener("click", async () => {
      if (!notifySupported()) return;
      if (Notification.permission === "denied") {
        alert("Las notificaciones están bloqueadas. Habilítalas en los ajustes del sitio de tu navegador.");
        return;
      }
      if (Notification.permission === "default") {
        const perm = await Notification.requestPermission();
        if (perm !== "granted") { renderBell(btn); return; }
      }
      const on = localStorage.getItem(NOTIFY_KEY) === "1";
      localStorage.setItem(NOTIFY_KEY, on ? "0" : "1");
      renderBell(btn);
      if (!on) {
        try {
          new Notification("Alertas de PulseGuard activadas", {
            body: "Te avisaremos cuando ingrese un paciente a emergencia.",
            icon: "/favicon.png",
          });
        } catch (e) {}
      }
    });
  }

  function notify(title, body, tag) {
    if (!notifyEnabled()) return;
    try {
      const n = new Notification(title, {
        body,
        icon: "/favicon.png",
        badge: "/favicon-32.png",
        tag,
      });
      n.onclick = () => { window.focus(); n.close(); };
    } catch (e) {}
  }

  /* ---------- autocompletado propio (estilizado) ---------- */
  function autocomplete(input, options, onSelect) {
    const wrap = document.createElement("div");
    wrap.className = "ac";
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);

    const list = document.createElement("div");
    list.className = "ac-list";
    wrap.appendChild(list);

    let items = [];
    let active = -1;
    let isOpen = false;

    const highlight = (text, q) => {
      const t = String(text == null ? "" : text);
      if (!q) return esc(t);
      const i = t.toLowerCase().indexOf(q);
      if (i < 0) return esc(t);
      return esc(t.slice(0, i)) + "<mark>" + esc(t.slice(i, i + q.length)) + "</mark>" + esc(t.slice(i + q.length));
    };

    function close() {
      list.classList.remove("open");
      isOpen = false;
      active = -1;
    }

    function render(value) {
      const q = (value || "").trim().toLowerCase();
      items = options.filter(
        (o) =>
          !q ||
          String(o.value).toLowerCase().includes(q) ||
          String(o.label || "").toLowerCase().includes(q)
      );
      if (!items.length) { close(); return; }
      active = -1;
      list.innerHTML = items
        .map(
          (o, i) => `<div class="ac-item" data-i="${i}">
            <span>${highlight(o.label || o.value, q)}</span>
            ${o.meta ? `<span class="ac-item__meta">${esc(o.meta)}</span>` : ""}
          </div>`
        )
        .join("");
      list.classList.add("open");
      isOpen = true;
    }

    function setActive(i) {
      const nodes = list.querySelectorAll(".ac-item");
      if (!nodes.length) return;
      if (active >= 0 && nodes[active]) nodes[active].classList.remove("active");
      active = (i + nodes.length) % nodes.length;
      nodes[active].classList.add("active");
      nodes[active].scrollIntoView({ block: "nearest" });
    }

    function choose(i) {
      const o = items[i];
      if (!o) return;
      input.value = o.value;
      close();
      if (onSelect) onSelect(o);
    }

    input.addEventListener("input", () => render(input.value));
    input.addEventListener("focus", () => render(input.value));
    input.addEventListener("blur", () => setTimeout(close, 140));
    input.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        if (!isOpen) render(input.value);
        setActive(active + 1);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        if (!isOpen) render(input.value);
        setActive(active - 1);
      } else if (e.key === "Enter") {
        if (isOpen && active >= 0) { e.preventDefault(); choose(active); }
      } else if (e.key === "Escape") {
        close();
      }
    });

    list.addEventListener("mousedown", (e) => {
      const item = e.target.closest(".ac-item");
      if (!item) return;
      e.preventDefault();
      choose(Number(item.dataset.i));
    });
  }

  return {
    API_BASE, PATIENTS, LEVEL, esc, fmtTime, patientName, levelInfo,
    checkHealth, connectWs, apiGet, toast, initNotify, notify, autocomplete,
    loadPatients,
  };
})();
