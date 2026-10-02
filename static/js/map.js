/* MODULE 2a — Regional map, and MODULE 2b — Getting to your island accordion. */
(() => {
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ------------------------------------------------------------------ map */
  const svg = document.getElementById("region-map");
  const card = document.getElementById("map-card");
  const dataEl = document.getElementById("map-data");

  if (card && dataEl) {
    const data = JSON.parse(dataEl.textContent || "{}");
    const nameEl = document.getElementById("map-card-name");
    const introEl = document.getElementById("map-card-intro");
    const accessEl = document.getElementById("map-card-access");
    const imgEl = document.getElementById("map-card-img");
    const chipsEl = document.getElementById("map-card-chips");
    const ctaEl = document.getElementById("map-card-cta");
    const closeBtn = document.getElementById("map-card-close");
    const listItems = document.querySelectorAll(".map-list__item");
    let currentSlug = null;

    const routeOf = (slug) => svg && svg.querySelector(`.isle-dot[data-slug="${slug}"] .isle-route`);

    const clearActive = () => {
      if (svg) {
        svg.classList.remove("has-active");
        svg.querySelectorAll(".isle-dot.is-active").forEach((el) => el.classList.remove("is-active"));
        svg.querySelectorAll(".isle-route.is-drawn").forEach((el) => el.classList.remove("is-drawn"));
      }
      listItems.forEach((b) => {
        b.classList.remove("is-active");
        b.setAttribute("aria-expanded", "false");
      });
    };

    const openIsland = (slug, fromList) => {
      const info = data[slug];
      if (!info) return;
      currentSlug = slug;
      clearActive();

      if (svg) {
        const dot = svg.querySelector(`.isle-dot[data-slug="${slug}"]`);
        if (dot) dot.classList.add("is-active");
        svg.classList.add("has-active");
        const route = routeOf(slug);
        if (route) route.classList.add("is-drawn");
      }
      listItems.forEach((b) => {
        const on = b.dataset.slug === slug;
        b.classList.toggle("is-active", on);
        b.setAttribute("aria-expanded", on ? "true" : "false");
      });

      nameEl.textContent = info.name;
      introEl.textContent = info.intro;
      if (accessEl) accessEl.textContent = info.access || "";
      if (imgEl && info.image) {
        imgEl.src = info.image;
        imgEl.alt = info.name;
      }
      chipsEl.innerHTML = "";
      (info.chips || []).forEach((chip) => {
        const span = document.createElement("span");
        span.className = "map-chip";
        span.textContent = `${chip.mode.toUpperCase()} ${chip.time} / ${chip.note}`;
        chipsEl.appendChild(span);
      });
      ctaEl.href = info.url;

      // Re-trigger the entrance animation.
      card.hidden = true;
      void card.offsetWidth;
      card.hidden = false;

      if (fromList && window.matchMedia("(max-width: 1000px)").matches) {
        const top = card.getBoundingClientRect().top;
        if (top > window.innerHeight * 0.7 || top < 0) {
          if (window.CI && window.CI.scrollTo) window.CI.scrollTo(card, -120);
          else card.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "center" });
        }
      }
    };

    const closeCard = () => {
      card.hidden = true;
      clearActive();
      if (currentSlug) {
        const btn = document.querySelector(`.map-list__item[data-slug="${currentSlug}"]`);
        if (btn) btn.focus({ preventScroll: true });
      }
      currentSlug = null;
    };

    if (svg) {
      svg.querySelectorAll(".isle-dot").forEach((dot) => {
        const slug = dot.dataset.slug;
        dot.addEventListener("click", () => openIsland(slug));
        dot.addEventListener("keydown", (e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            openIsland(slug);
          }
        });
        const hoverOn = () => {
          const r = routeOf(slug);
          if (r) r.classList.add("is-drawn");
        };
        const hoverOff = () => {
          if (slug === currentSlug) return;
          const r = routeOf(slug);
          if (r) r.classList.remove("is-drawn");
        };
        dot.addEventListener("mouseenter", hoverOn);
        dot.addEventListener("mouseleave", hoverOff);
        dot.addEventListener("focus", hoverOn);
        dot.addEventListener("blur", hoverOff);
      });
    }

    listItems.forEach((btn) => {
      btn.addEventListener("click", () => openIsland(btn.dataset.slug, true));
      btn.addEventListener("mouseenter", () => {
        const r = routeOf(btn.dataset.slug);
        if (r) r.classList.add("is-drawn");
      });
      btn.addEventListener("mouseleave", () => {
        if (btn.dataset.slug === currentSlug) return;
        const r = routeOf(btn.dataset.slug);
        if (r) r.classList.remove("is-drawn");
      });
    });

    if (closeBtn) closeBtn.addEventListener("click", closeCard);
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !card.hidden && window.matchMedia("(max-width: 1000px)").matches) closeCard();
    });

    // Open the first island by default on wide screens so the module never looks empty.
    // [data-slug]: the unlabelled extra islands (Saba, Guadeloupe...) share the
    // .isle-dot class, render first, and have no destination data.
    const first = svg && svg.querySelector(".isle-dot[data-slug]");
    if (first && window.matchMedia("(min-width: 1001px)").matches) openIsland(first.dataset.slug);
  }

  /* ------------------------------------------------ getting there accordion */
  /* Direct flights only. Opening an island draws its routes in #route-diagram;
     choosing a departure city highlights that one route. Data comes from the
     #airlift-data JSON block (routes/main.py build_airlift_data). */
  const acc = document.querySelector("[data-accordion]");
  if (!acc) return;

  const items = Array.from(acc.querySelectorAll(".access-acc__item"));
  const diagram = document.getElementById("route-diagram");
  const airliftEl = document.getElementById("airlift-data");
  const airlift = airliftEl ? JSON.parse(airliftEl.textContent || "{}") : {};
  const NS = "http://www.w3.org/2000/svg";
  const W = 460, H = 560, CITY_X = 34, ISLE_X = 418, TOP = 46, BOTTOM = 516;

  const emptyMessage = (diagram && diagram.querySelector(".route-empty")
    ? diagram.querySelector(".route-empty").textContent
    : "Open an island to see its direct routes");

  let drawnSlug = null;
  let activeCity = null;

  const el = (name, attrs, text) => {
    const node = document.createElementNS(NS, name);
    Object.entries(attrs || {}).forEach(([k, v]) => node.setAttribute(k, v));
    if (text != null) node.textContent = text;
    return node;
  };

  const clearDiagram = (message) => {
    if (!diagram) return;
    diagram.innerHTML = "";
    drawnSlug = null;
    activeCity = null;
    if (message) {
      diagram.appendChild(el("text", { x: W / 2, y: H / 2, "text-anchor": "middle", class: "route-empty" }, message));
    }
  };

  const draw = (slug) => {
    if (!diagram) return;
    const info = airlift[slug];
    if (!info) return clearDiagram("");
    diagram.innerHTML = "";
    drawnSlug = slug;
    activeCity = null;

    const routes = info.routes || [];
    const isleY = H / 2;
    const step = routes.length > 1 ? (BOTTOM - TOP) / (routes.length - 1) : 0;

    routes.forEach((route, i) => {
      const y = routes.length > 1 ? TOP + i * step : isleY;
      const group = el("g", { class: "route-city", "data-city": route.city, tabindex: "0",
                             role: "button", "aria-label": `${route.city} to ${info.name}, ${route.time} nonstop` });

      group.appendChild(el("path", {
        class: "route-line",
        "data-city": route.city,
        d: `M${CITY_X + 6},${y} C ${W * 0.45},${y} ${W * 0.55},${isleY} ${ISLE_X - 10},${isleY}`,
      }));
      group.appendChild(el("circle", { class: "route-dot", "data-city": route.city, cx: CITY_X + 6, cy: y, r: 3.5 }));
      group.appendChild(el("text", { class: "route-label", "data-city": route.city, x: CITY_X + 16, y: y - 7 }, route.city));
      group.appendChild(el("text", { class: "route-time", "data-city": route.city, x: CITY_X + 16, y: y + 9 },
                          route.seasonal ? `${route.time} · Seasonal*` : route.time));
      diagram.appendChild(group);

      group.addEventListener("click", () => select(slug, route.city, true));
      group.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select(slug, route.city, true); }
      });
    });

    const isle = el("g", { class: "route-isle" });
    isle.appendChild(el("circle", { class: "route-dot route-dot--island", cx: ISLE_X, cy: isleY, r: 6 }));
    isle.appendChild(el("text", { class: "route-label route-label--island", x: ISLE_X, y: isleY - 18,
                                  "text-anchor": "middle" }, info.name.split(" / ")[0].split(" — ")[0]));
    if (info.code) {
      isle.appendChild(el("text", { class: "route-code", x: ISLE_X, y: isleY + 24, "text-anchor": "middle" }, info.code));
    }
    diagram.appendChild(isle);
  };

  /* Highlight one route, in the diagram and in the open panel. */
  const select = (slug, city, fromDiagram) => {
    if (drawnSlug !== slug) draw(slug);
    activeCity = activeCity === city ? null : city;

    diagram && diagram.querySelectorAll("[data-city]").forEach((node) => {
      node.classList.toggle("is-highlighted", !!activeCity && node.dataset.city === activeCity);
    });
    acc.querySelectorAll(".airlift__route").forEach((btn) => {
      btn.classList.toggle("is-active", !!activeCity && btn.dataset.slug === slug && btn.dataset.city === activeCity);
    });

    if (!fromDiagram || !activeCity) return;
    const btn = acc.querySelector(`.airlift__route[data-slug="${slug}"][data-city="${CSS.escape(activeCity)}"]`);
    if (btn) btn.focus({ preventScroll: true });
  };

  const setOpen = (item, open) => {
    const btn = item.querySelector(".access-acc__btn");
    const panel = item.querySelector(".access-acc__panel");
    if (!btn || !panel) return;
    const isOpen = item.classList.contains("is-open");
    if (open === isOpen) return;
    item.classList.toggle("is-open", open);
    btn.setAttribute("aria-expanded", open ? "true" : "false");

    if (reduce || !panel.animate) {
      panel.hidden = !open;
      return;
    }
    if (open) {
      panel.hidden = false;
      const h = panel.scrollHeight;
      panel.animate([{ height: "0px", opacity: 0 }, { height: `${h}px`, opacity: 1 }], { duration: 650, easing: "cubic-bezier(.16,1,.3,1)" });
    } else {
      const h = panel.scrollHeight;
      const anim = panel.animate([{ height: `${h}px`, opacity: 1 }, { height: "0px", opacity: 0 }], { duration: 450, easing: "cubic-bezier(.65,0,.35,1)" });
      anim.onfinish = () => {
        if (!item.classList.contains("is-open")) panel.hidden = true;
      };
    }
  };

  items.forEach((item) => {
    const btn = item.querySelector(".access-acc__btn");
    btn.addEventListener("click", () => {
      const willOpen = !item.classList.contains("is-open");
      items.forEach((other) => other !== item && setOpen(other, false));
      setOpen(item, willOpen);
      if (willOpen) draw(item.dataset.slug);
      else clearDiagram(emptyMessage);
    });

    item.querySelectorAll(".airlift__route").forEach((route) => {
      route.addEventListener("click", () => select(route.dataset.slug, route.dataset.city, false));
    });
  });

  // Open the first island so the diagram is never empty on a wide screen.
  const first = items[0];
  if (first && window.matchMedia("(min-width: 1001px)").matches) {
    setOpen(first, true);
    draw(first.dataset.slug);
  }
})();
