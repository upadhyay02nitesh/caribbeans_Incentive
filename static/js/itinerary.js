/* MODULE 4 — Five-day itinerary. User-driven (no auto-advance). */
(() => {
  const tabs = Array.from(document.querySelectorAll("#itin-tabs .itin-tab"));
  const dataEl = document.getElementById("itinerary-data");
  const img = document.getElementById("itin-img");
  const dayEl = document.getElementById("itin-day");
  const titleEl = document.getElementById("itin-title");
  const descEl = document.getElementById("itin-desc");
  const bigEl = document.getElementById("itin-big");
  const fill = document.getElementById("itin-fill");
  if (!tabs.length || !dataEl || !img) return;

  const days = JSON.parse(dataEl.textContent || "[]");
  const body = titleEl.closest(".itin-panel__body");
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let current = 0;
  let swapTimer = null;

  // Warm the cache so swaps are instant.
  days.forEach((d) => {
    if (d.image) new Image().src = d.image;
  });

  const setDay = (index, focusTab) => {
    const d = days[index];
    if (!d || index === current) return;
    current = index;

    tabs.forEach((t, i) => {
      const on = i === index;
      t.classList.toggle("is-active", on);
      t.setAttribute("aria-selected", on ? "true" : "false");
      t.tabIndex = on ? 0 : -1;
    });
    if (focusTab) tabs[index].focus();
    if (fill) fill.style.transform = `translateX(${index * 100}%)`;
    if (tabs[index].scrollIntoView && window.matchMedia("(max-width: 900px)").matches) {
      tabs[index].scrollIntoView({ inline: "center", block: "nearest", behavior: reduce ? "auto" : "smooth" });
    }

    const apply = () => {
      img.src = d.image || img.src;
      img.alt = `${d.day} — ${d.title}`;
      dayEl.textContent = d.day;
      titleEl.textContent = d.title;
      descEl.textContent = d.desc;
      if (bigEl) bigEl.textContent = String(index + 1).padStart(2, "0");
    };

    if (reduce) {
      apply();
      return;
    }
    window.clearTimeout(swapTimer);
    img.classList.add("is-swapping");
    if (body) body.classList.add("is-swapping");
    swapTimer = window.setTimeout(() => {
      apply();
      img.classList.remove("is-swapping");
      if (body) body.classList.remove("is-swapping");
    }, 420);
  };

  tabs.forEach((tab) => tab.addEventListener("click", () => setDay(Number(tab.dataset.index))));

  document.getElementById("itin-tabs").addEventListener("keydown", (e) => {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    e.preventDefault();
    const dir = e.key === "ArrowRight" ? 1 : -1;
    setDay((current + dir + days.length) % days.length, true);
  });

  document.querySelectorAll("[data-itin-step]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const dir = Number(btn.dataset.itinStep);
      setDay((current + dir + days.length) % days.length);
    });
  });
})();
