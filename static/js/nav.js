/* Header state, full-screen menu, page transitions, custom cursor, inquiry pill. */
(() => {
  const html = document.documentElement;
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const CI = (window.CI = window.CI || {});

  /* --------------------------------------------------------------- header */
  const header = document.getElementById("site-nav");
  const fab = document.getElementById("inquiry-fab");
  let lastY = window.scrollY;
  const onScroll = () => {
    const y = window.scrollY;
    if (header) {
      header.classList.toggle("is-scrolled", y > 40);
      const hide = y > 320 && y > lastY + 2 && !html.classList.contains("menu-open");
      const show = y < lastY - 2 || y <= 320;
      if (hide) header.classList.add("is-hidden");
      else if (show) header.classList.remove("is-hidden");
      html.classList.toggle("header-visible", !header.classList.contains("is-hidden") && y > 40);
      html.style.setProperty("--header-offset", `${header.offsetHeight - 1}px`);
    }
    if (fab) fab.classList.toggle("is-visible", y > window.innerHeight * 0.6 && !fab.dataset.suppressed);
    lastY = y;
  };
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  // Keep the pill out of the way where an estimate/footer CTA is already on screen.
  if (fab && "IntersectionObserver" in window) {
    const blockers = document.querySelectorAll("#estimator, .site-footer, .connect");
    const visible = new Set();
    const bio = new IntersectionObserver((entries) => {
      entries.forEach((e) => (e.isIntersecting ? visible.add(e.target) : visible.delete(e.target)));
      if (visible.size) fab.dataset.suppressed = "1";
      else delete fab.dataset.suppressed;
      onScroll();
    });
    blockers.forEach((b) => bio.observe(b));
    fab.addEventListener("click", (e) => {
      const target = document.getElementById("estimator");
      if (target && CI.scrollTo) {
        e.preventDefault();
        CI.scrollTo(target, -40);
      }
    });
  }

  /* ------------------------------------------------- header nav dropdown */
  // Hover/focus is CSS; this adds tap-to-open on touch and Esc to close.
  document.querySelectorAll("[data-nav-drop]").forEach((item) => {
    const trigger = item.querySelector("[data-nav-drop-trigger]");
    if (!trigger) return;
    const setOpen = (open) => {
      item.classList.toggle("is-open", open);
      trigger.setAttribute("aria-expanded", open ? "true" : "false");
    };
    trigger.addEventListener("click", (e) => {
      if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;
      if (!item.classList.contains("is-open")) {
        e.preventDefault();
        setOpen(true);
      }
    });
    item.addEventListener("mouseenter", () => setOpen(true));
    item.addEventListener("mouseleave", () => setOpen(false));
    item.addEventListener("focusout", (e) => {
      if (!item.contains(e.relatedTarget)) setOpen(false);
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && item.classList.contains("is-open")) {
        setOpen(false);
        trigger.focus({ preventScroll: true });
      }
    });
    document.addEventListener("click", (e) => {
      if (!item.contains(e.target)) setOpen(false);
    });
  });

  /* ----------------------------------------------------------------- menu */
  const toggle = document.getElementById("menu-toggle");
  const menu = document.getElementById("site-menu");
  if (toggle && menu) {
    let closeTimer = null;
    const focusables = () => Array.from(menu.querySelectorAll("a, button")).concat([toggle]);

    const open = () => {
      window.clearTimeout(closeTimer);
      menu.hidden = false;
      void menu.offsetWidth;
      menu.classList.add("is-open");
      toggle.setAttribute("aria-expanded", "true");
      html.classList.add("menu-open");
      if (CI.lenis) CI.lenis.stop();
      else document.body.style.overflow = "hidden";
      const first = menu.querySelector(".site-menu__link");
      window.setTimeout(() => first && first.focus({ preventScroll: true }), 400);
    };
    const close = (returnFocus = true) => {
      menu.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
      html.classList.remove("menu-open");
      if (CI.lenis) CI.lenis.start();
      else document.body.style.overflow = "";
      closeTimer = window.setTimeout(() => (menu.hidden = true), reduce ? 0 : 900);
      if (returnFocus) toggle.focus({ preventScroll: true });
    };

    toggle.addEventListener("click", () => (menu.classList.contains("is-open") ? close() : open()));
    document.addEventListener("keydown", (e) => {
      if (!menu.classList.contains("is-open")) return;
      if (e.key === "Escape") close();
      if (e.key === "Tab") {
        const items = focusables();
        const idx = items.indexOf(document.activeElement);
        if (e.shiftKey && idx <= 0) {
          e.preventDefault();
          items[items.length - 1].focus();
        } else if (!e.shiftKey && idx === items.length - 1) {
          e.preventDefault();
          items[0].focus();
        }
      }
    });

    const imgs = menu.querySelectorAll("[data-menu-img]");
    menu.querySelectorAll("[data-menu-index]").forEach((link) => {
      const activate = () => imgs.forEach((im) => im.classList.toggle("is-active", im.dataset.menuImg === link.dataset.menuIndex));
      link.addEventListener("pointerenter", activate);
      link.addEventListener("focus", activate);
    });
  }

  /* Page transitions removed by request — internal links now navigate
     immediately, no curtain cover/delay on click and no reveal wipe on load
     (see the matching CSS change: .curtain is hidden unconditionally). */

  /* --------------------------------------------------------------- cursor */
  const fine = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  const cursor = document.querySelector(".cursor");
  if (cursor && fine && !reduce) {
    html.classList.add("has-cursor");
    const dot = cursor.querySelector(".cursor__dot");
    const ring = cursor.querySelector(".cursor__ring");
    const label = cursor.querySelector(".cursor__label");
    let mx = -100, my = -100, rx = -100, ry = -100;
    window.addEventListener("pointermove", (e) => {
      mx = e.clientX;
      my = e.clientY;
      dot.style.transform = `translate3d(${mx}px, ${my}px, 0)`;
    }, { passive: true });
    const loop = () => {
      rx += (mx - rx) * 0.18;
      ry += (my - ry) * 0.18;
      ring.style.transform = `translate3d(${rx}px, ${ry}px, 0)`;
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);

    document.addEventListener("pointerover", (e) => {
      const labelled = e.target.closest("[data-cursor]");
      const interactive = e.target.closest("a, button, input, select, textarea, label, [role='button']");
      if (labelled) {
        label.textContent = labelled.dataset.cursor;
        html.classList.add("cursor-label");
        html.classList.remove("cursor-link");
      } else {
        html.classList.remove("cursor-label");
        html.classList.toggle("cursor-link", !!interactive);
      }
    });
    document.documentElement.addEventListener("pointerleave", () => html.classList.add("cursor-hidden"));
    document.documentElement.addEventListener("pointerenter", () => html.classList.remove("cursor-hidden"));
  }
})();
