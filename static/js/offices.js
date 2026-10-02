/* Office map on /lets-connect — the office buttons move the embedded map. */
(() => {
  const frame = document.getElementById("office-map");
  const buttons = document.querySelectorAll(".office[data-map-src]");
  if (!frame || !buttons.length) return;

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      if (btn.getAttribute("aria-pressed") === "true") return;
      buttons.forEach((b) => b.setAttribute("aria-pressed", b === btn ? "true" : "false"));
      frame.src = btn.dataset.mapSrc;
      frame.title = `Map of our ${btn.querySelector(".office__name").textContent} office`;
    });
  });
})();
