/* Caribbean Incentive — admin.js
   Shell behaviour + hand-rendered SVG charts for the demo admin.
   Everything degrades: numbers are rendered server-side, charts simply
   don't draw without JS, and the reveal class is only added by JS. */
(function () {
  const root = document.documentElement;
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const NS = "http://www.w3.org/2000/svg";

  const el = (tag, attrs, parent) => {
    const node = document.createElementNS(NS, tag);
    for (const k in attrs) node.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(node);
    return node;
  };
  const fmtInt = (n) => Math.round(n).toLocaleString("en-US");
  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const fmtDay = (iso) => `${+iso.slice(8, 10)} ${MONTHS[+iso.slice(5, 7) - 1]}`;
  const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const weekday = (iso) => WEEKDAYS[new Date(iso + "T12:00:00").getDay()];

  /* ---------------------------------------------------------------- shell */
  const shell = document.querySelector("[data-shell]");
  const toggle = document.querySelector("[data-nav-toggle]");
  if (shell && toggle) {
    const setOpen = (open) => {
      shell.classList.toggle("is-nav-open", open);
      toggle.setAttribute("aria-expanded", String(open));
    };
    toggle.addEventListener("click", () => setOpen(!shell.classList.contains("is-nav-open")));
    document.querySelectorAll("[data-nav-close]").forEach((n) => n.addEventListener("click", () => setOpen(false)));
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") setOpen(false); });
  }

  const search = document.querySelector("[data-search]");
  document.addEventListener("keydown", (e) => {
    if (e.key !== "/" || !search) return;
    const t = e.target;
    if (t.matches("input, textarea, select") || t.isContentEditable) return;
    e.preventDefault();
    search.focus();
  });

  // Clickable table rows (keyboard accessible)
  document.querySelectorAll("[data-href]").forEach((row) => {
    row.tabIndex = 0;
    row.addEventListener("click", (e) => { if (!e.target.closest("a")) window.location = row.dataset.href; });
    row.addEventListener("keydown", (e) => { if (e.key === "Enter") window.location = row.dataset.href; });
  });

  /* ----------------------------------------------------- count-up numbers */
  const countUp = (node) => {
    const target = parseFloat(node.dataset.count);
    const prefix = node.dataset.prefix || "";
    const suffix = node.dataset.suffix || "";
    const decimals = +(node.dataset.decimals || 0);
    const final = node.innerHTML;  // keeps unit labels like <small>submitted</small>
    const unit = node.querySelector("small");
    const tail = unit ? " " + unit.outerHTML : "";
    if (reduced || isNaN(target)) return;
    const start = performance.now();
    const dur = 1500;
    const tick = (now) => {
      const p = Math.min(1, (now - start) / dur);
      const eased = 1 - Math.pow(1 - p, 4);
      const v = target * eased;
      node.innerHTML = prefix + (decimals ? v.toFixed(decimals) : fmtInt(v)) + suffix + tail;
      if (p < 1) requestAnimationFrame(tick);
      else node.innerHTML = final;
    };
    requestAnimationFrame(tick);
  };
  document.querySelectorAll("[data-count]").forEach(countUp);

  /* ------------------------------------------------------------ ring gauge */
  document.querySelectorAll("[data-ring]").forEach((ring) => {
    const pct = Math.max(0, Math.min(100, parseFloat(ring.dataset.ring)));
    const bar = ring.querySelector(".ring__bar");
    const c = 2 * Math.PI * 42;
    bar.style.strokeDasharray = c;
    bar.style.strokeDashoffset = c;
    requestAnimationFrame(() => requestAnimationFrame(() => {
      bar.style.strokeDashoffset = c * (1 - pct / 100);
    }));
  });

  /* ----------------------------------------------------------- sparklines */
  const sparkline = (host, values, opts) => {
    const W = 150, H = 44, pad = 3;
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, preserveAspectRatio: "none", "aria-hidden": "true" }, host);
    const max = Math.max(...values, 1);
    if (opts.type === "bars") {
      const gap = 2;
      const bw = (W - gap * (values.length - 1)) / values.length;
      values.forEach((v, i) => {
        const h = v ? Math.max(4, (v / max) * (H - pad)) : 2;
        el("rect", { x: i * (bw + gap), y: H - h, width: bw, height: h, rx: Math.min(2, bw / 2),
          fill: v ? opts.color : "rgba(255,255,255,.1)" }, svg);
      });
      return;
    }
    const min = opts.zero ? 0 : Math.min(...values);
    const x = (i) => (i / (values.length - 1)) * W;
    const y = (v) => H - pad - ((v - min) / (max - min || 1)) * (H - pad * 2);
    const pts = values.map((v, i) => [x(i), y(v)]);
    const line = opts.step
      ? pts.map((p, i) => (i ? `H${p[0]}V${p[1]}` : `M${p[0]},${p[1]}`)).join("")
      : pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join("");
    const id = "sg" + Math.random().toString(36).slice(2, 8);
    const defs = el("defs", {}, svg);
    const grad = el("linearGradient", { id, x1: 0, x2: 0, y1: 0, y2: 1 }, defs);
    el("stop", { offset: "0", "stop-color": opts.color, "stop-opacity": ".35" }, grad);
    el("stop", { offset: "1", "stop-color": opts.color, "stop-opacity": "0" }, grad);
    el("path", { d: `${line}L${W},${H}L0,${H}Z`, fill: `url(#${id})` }, svg);
    const path = el("path", { d: line, fill: "none", stroke: opts.color, "stroke-width": 2,
      "stroke-linejoin": "round", "stroke-linecap": "round", "vector-effect": "non-scaling-stroke" }, svg);
    const last = pts[pts.length - 1];
    if (!reduced && path.getTotalLength) {
      const len = path.getTotalLength();
      path.style.strokeDasharray = len;
      path.style.strokeDashoffset = len;
      path.getBoundingClientRect();
      path.style.transition = "stroke-dashoffset 1.6s cubic-bezier(.16,1,.3,1) .2s";
      path.style.strokeDashoffset = 0;
    }
    el("circle", { cx: last[0], cy: last[1], r: 3, fill: opts.color, stroke: "#161F3B", "stroke-width": 2,
      "vector-effect": "non-scaling-stroke" }, svg);
  };

  /* ------------------------------------------------ area chart w/ tooltip */
  const areaChart = (host, days, values, opts) => {
    host.textContent = "";
    const rect = host.getBoundingClientRect();
    const W = Math.max(280, rect.width), H = rect.height || 290;
    const m = { t: 16, r: 8, b: 28, l: 34 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const niceMax = Math.max(10, Math.ceil(Math.max(...values) * 1.15 / 10) * 10);
    const x = (i) => m.l + (i / (values.length - 1)) * iw;
    const y = (v) => m.t + ih - (v / niceMax) * ih;

    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": opts.label }, host);
    const ticks = 4;
    for (let t = 0; t <= ticks; t++) {
      const v = (niceMax / ticks) * t;
      el("line", { class: "grid-line", x1: m.l, x2: W - m.r, y1: y(v), y2: y(v) }, svg);
      el("text", { class: "axis-text", x: m.l - 10, y: y(v) + 4, "text-anchor": "end" }, svg).textContent = fmtInt(v);
    }
    const every = W < 520 ? 4 : 2;
    days.forEach((d, i) => {
      const last = days.length - 1;
      if (i !== last && (i % every || last - i < every)) return;
      el("text", { class: "axis-text", x: x(i), y: H - 6, "text-anchor": i === 0 ? "start" : i === days.length - 1 ? "end" : "middle" }, svg)
        .textContent = fmtDay(d);
    });

    const pts = values.map((v, i) => [x(i), y(v)]);
    // Smooth monotone-ish curve via Catmull-Rom → Bézier
    let d = `M${pts[0][0]},${pts[0][1]}`;
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2;
      const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
      const c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
      d += `C${c1[0].toFixed(1)},${c1[1].toFixed(1)} ${c2[0].toFixed(1)},${c2[1].toFixed(1)} ${p2[0].toFixed(1)},${p2[1].toFixed(1)}`;
    }
    const defs = el("defs", {}, svg);
    const grad = el("linearGradient", { id: "area-grad", x1: 0, x2: 0, y1: 0, y2: 1 }, defs);
    el("stop", { offset: "0", "stop-color": "#2BB5AE", "stop-opacity": ".38" }, grad);
    el("stop", { offset: "1", "stop-color": "#2BB5AE", "stop-opacity": "0" }, grad);
    const clip = el("clipPath", { id: "area-clip" }, defs);
    const clipRect = el("rect", { x: 0, y: 0, width: reduced ? W : 0, height: H }, clip);
    const g = el("g", { "clip-path": "url(#area-clip)" }, svg);
    el("path", { d: `${d}L${x(values.length - 1)},${m.t + ih}L${m.l},${m.t + ih}Z`, fill: "url(#area-grad)" }, g);
    el("path", { d, class: "series-line" }, g);
    if (!reduced) {
      const t0 = performance.now();
      const grow = (now) => {
        const p = Math.min(1, (now - t0) / 1400);
        clipRect.setAttribute("width", W * (1 - Math.pow(1 - p, 3)));
        if (p < 1) requestAnimationFrame(grow);
      };
      requestAnimationFrame(grow);
    }

    // peak label (selective direct label)
    const peak = values.indexOf(Math.max(...values));
    el("circle", { class: "dot", cx: pts[peak][0], cy: pts[peak][1], r: 4 }, svg);
    el("text", { class: "axis-text", x: pts[peak][0], y: pts[peak][1] - 12, "text-anchor": "middle", fill: "#F3D59E",
      style: "fill:#F3D59E;font-weight:600" }, svg).textContent = `Peak ${values[peak]}`;

    // hover layer
    const cross = el("line", { class: "crosshair", y1: m.t, y2: m.t + ih, opacity: 0 }, svg);
    const dot = el("circle", { class: "dot", r: 5, opacity: 0 }, svg);
    const tip = document.createElement("div");
    tip.className = "chart-tip";
    host.appendChild(tip);
    const hit = el("rect", { x: m.l, y: 0, width: iw, height: H, fill: "transparent" }, svg);
    const show = (clientX) => {
      const r = svg.getBoundingClientRect();
      const px = ((clientX - r.left) / r.width) * W;
      const i = Math.max(0, Math.min(values.length - 1, Math.round(((px - m.l) / iw) * (values.length - 1))));
      const [cx, cy] = pts[i];
      cross.setAttribute("x1", cx); cross.setAttribute("x2", cx); cross.setAttribute("opacity", 1);
      dot.setAttribute("cx", cx); dot.setAttribute("cy", cy); dot.setAttribute("opacity", 1);
      const prev = i > 0 ? values[i] - values[i - 1] : null;
      const change = prev === null ? "" : ` <span style="color:${prev >= 0 ? "#8FE3B3" : "#F29A86"}">${prev >= 0 ? "▲" : "▼"} ${Math.abs(prev)}</span>`;
      tip.innerHTML = `${weekday(days[i])} ${fmtDay(days[i])}<strong>${fmtInt(values[i])} ${opts.unit}${change}</strong>`;
      tip.style.left = `${(cx / W) * 100}%`;
      tip.style.top = `${(cy / H) * 100}%`;
      tip.classList.add("is-on");
    };
    const hide = () => { cross.setAttribute("opacity", 0); dot.setAttribute("opacity", 0); tip.classList.remove("is-on"); };
    hit.addEventListener("pointermove", (e) => show(e.clientX));
    hit.addEventListener("pointerleave", hide);
  };

  /* -------------------------------------------------------------- donut */
  const donut = (host) => {
    // accepts {label, value, color?} or the traffic-source shape {source, visitors}
    const data = JSON.parse(host.dataset.donut).map((d) => ({ label: d.label ?? d.source, value: d.value ?? d.visitors, color: d.color }));
    const colors = ["var(--s1)", "var(--s2)", "var(--s3)", "var(--s4)", "var(--s5)"];
    const total = data.reduce((s, d) => s + d.value, 0);
    if (!total) return; // no traffic yet — leave the empty centre label
    const plot = host.querySelector(".donut__plot");
    const list = host.querySelector(".donut__list");
    const svg = el("svg", { viewBox: "0 0 170 170", role: "img", "aria-label": host.dataset.label }, plot);
    const cx = 85, cy = 85, R = 80, r = 58, gapA = 0.025;
    let a = -Math.PI / 2;
    const arc = (a0, a1) => {
      const p = (rad, ang) => [cx + rad * Math.cos(ang), cy + rad * Math.sin(ang)];
      const large = a1 - a0 > Math.PI ? 1 : 0;
      const [x0, y0] = p(R, a0), [x1, y1] = p(R, a1), [x2, y2] = p(r, a1), [x3, y3] = p(r, a0);
      return `M${x0},${y0}A${R},${R} 0 ${large} 1 ${x1},${y1}L${x2},${y2}A${r},${r} 0 ${large} 0 ${x3},${y3}Z`;
    };
    const center = host.querySelector(".donut__center");
    const centerDefault = center.innerHTML;
    data.forEach((d, i) => {
      const span = (d.value / total) * Math.PI * 2;
      const path = el("path", { d: arc(a + gapA / 2, a + span - gapA / 2), style: `fill:${d.color || colors[i % colors.length]}` }, svg);
      a += span;
      const li = list.children[i];
      const on = () => {
        plot.classList.add("is-hover");
        path.classList.add("is-hot");
        li && li.classList.add("is-hot");
        center.innerHTML = `<strong>${Math.round((d.value / total) * 100)}%</strong><span>${d.label}</span>`;
      };
      const off = () => {
        plot.classList.remove("is-hover");
        path.classList.remove("is-hot");
        li && li.classList.remove("is-hot");
        center.innerHTML = centerDefault;
      };
      path.addEventListener("pointerenter", on);
      path.addEventListener("pointerleave", off);
      if (li) { li.addEventListener("pointerenter", on); li.addEventListener("pointerleave", off); }
    });
    if (!reduced) {
      svg.style.transform = "rotate(-40deg) scale(.9)";
      svg.style.opacity = "0";
      svg.getBoundingClientRect();
      svg.style.transition = "transform 1.4s cubic-bezier(.16,1,.3,1), opacity .8s";
      svg.style.transform = "none";
      svg.style.opacity = "1";
    }
  };

  /* ------------------------------------------------------------ wire up */
  const dataNode = document.getElementById("admin-chart-data");
  const chartData = dataNode ? JSON.parse(dataNode.textContent) : null;

  document.querySelectorAll("[data-spark]").forEach((host) => {
    if (!chartData) return;
    const values = chartData[host.dataset.spark];
    sparkline(host, values, {
      color: host.dataset.color || "#7FD8D0",
      type: host.dataset.type,
      step: host.dataset.type === "step",
      zero: true,
    });
  });

  document.querySelectorAll("[data-donut]").forEach(donut);

  const area = document.querySelector("[data-area]");
  if (area && chartData) {
    const series = { daily: chartData.sessions };
    const draw = () => areaChart(area, chartData.days, series.daily, { label: "Daily sessions, last 14 days", unit: "sessions" });
    draw();
    let rt;
    window.addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(draw, 150); });
  }

  /* ------------------------------------------- visitors filter + search */
  const table = document.querySelector("[data-filter-table]");
  if (table) {
    const rows = [...table.querySelectorAll("tbody tr[data-status]")];
    const chips = [...document.querySelectorAll("[data-filter]")];
    const input = document.querySelector("[data-table-search]");
    const empty = document.querySelector("[data-empty]");
    const params = new URLSearchParams(location.search);
    let status = "all";
    if (input && params.get("q")) input.value = params.get("q");
    const apply = () => {
      const q = (input ? input.value : "").trim().toLowerCase();
      let shown = 0;
      rows.forEach((row) => {
        const ok = (status === "all" || row.dataset.status === status) && (!q || row.dataset.text.includes(q));
        row.hidden = !ok;
        if (ok) shown++;
      });
      if (empty) empty.hidden = shown > 0;
    };
    chips.forEach((chip) => chip.addEventListener("click", () => {
      status = chip.dataset.filter;
      chips.forEach((c) => c.setAttribute("aria-pressed", String(c === chip)));
      apply();
    }));
    if (input) input.addEventListener("input", apply);
    apply();
  }

  requestAnimationFrame(() => requestAnimationFrame(() => root.classList.add("is-ready")));
})();
