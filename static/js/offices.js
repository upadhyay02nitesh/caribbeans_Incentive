/* Office map on /lets-connect — the office buttons move the embedded map. */
(() => {
  const frame = document.getElementById("office-map");
  const buttons = document.querySelectorAll(".office[data-map-src]");
  if (!frame) return;

  // The embed pulls ~2 MB of Google Maps code: load it only when the map is about to scroll into view.
  const load = () => { if (frame.dataset.src) { frame.src = frame.dataset.src; delete frame.dataset.src; } };
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      if (entries.some((e) => e.isIntersecting)) { load(); io.disconnect(); }
    }, { rootMargin: "400px 0px" });
    io.observe(frame);
  } else load();
  if (!buttons.length) return;

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      if (btn.getAttribute("aria-pressed") === "true") return;
      buttons.forEach((b) => b.setAttribute("aria-pressed", b === btn ? "true" : "false"));
      delete frame.dataset.src;
      frame.src = btn.dataset.mapSrc;
      frame.title = `Map of our ${btn.querySelector(".office__name").textContent} office`;
    });
  });
})();
