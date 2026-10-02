/* Let's Connect: tabs, client-side validation, RFP dropzone. Submission stays
   a normal POST — the server re-renders this page with the success panel. */
(() => {
  /* ----------------------------------------------------------------- tabs */
  const tablist = document.getElementById("connectTabs");
  if (tablist) {
    const tabs = Array.from(tablist.querySelectorAll("[role=tab]"));
    const ink = tablist.querySelector(".tabs__ink");
    const moveInk = (tab) => {
      if (!ink || !tab) return;
      ink.style.width = `${tab.offsetWidth - 28}px`;
      ink.style.transform = `translateX(${tab.offsetLeft}px)`;
    };
    const select = (tab, focus) => {
      tabs.forEach((t) => {
        const on = t === tab;
        t.classList.toggle("is-active", on);
        t.setAttribute("aria-selected", on ? "true" : "false");
        t.tabIndex = on ? 0 : -1;
        const pane = document.getElementById(t.dataset.tab);
        if (pane) {
          pane.hidden = !on;
          pane.classList.toggle("is-active", on);
        }
      });
      if (focus) tab.focus();
      moveInk(tab);
    };
    tabs.forEach((tab) => tab.addEventListener("click", () => select(tab)));
    tablist.addEventListener("keydown", (e) => {
      const idx = tabs.indexOf(document.activeElement);
      if (idx < 0) return;
      let next = null;
      if (e.key === "ArrowRight") next = tabs[(idx + 1) % tabs.length];
      if (e.key === "ArrowLeft") next = tabs[(idx - 1 + tabs.length) % tabs.length];
      if (e.key === "Home") next = tabs[0];
      if (e.key === "End") next = tabs[tabs.length - 1];
      if (next) {
        e.preventDefault();
        select(next, true);
      }
    });
    const fromHash = location.hash && tabs.find((t) => `#${t.dataset.tab}` === location.hash);
    const serverActive = tabs.find((t) => t.classList.contains("is-active")) || tabs[0];
    // A deep link (e.g. /lets-connect#tab-rfp) picks the tab unless the server
    // just rendered a submission result on another one.
    if (fromHash && !document.querySelector(".success-panel, .field__error")) select(fromHash);
    else moveInk(serverActive);
    window.addEventListener("hashchange", () => {
      const t = tabs.find((tab) => `#${tab.dataset.tab}` === location.hash);
      if (t) select(t);
    });
    window.addEventListener("resize", () => moveInk(tabs.find((t) => t.classList.contains("is-active"))));
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => moveInk(tabs.find((t) => t.classList.contains("is-active"))));
  }

  // A just-submitted form's success panel takes focus so it is announced.
  const success = document.querySelector(".tab-pane.is-active .success-panel");
  if (success) {
    success.focus({ preventScroll: true });
    const form = document.querySelector(".connect__form");
    if (form && window.matchMedia("(max-width: 1000px)").matches) form.scrollIntoView();
  }

  // Coming back via the browser's back button restores the page from cache with
  // the spinner still running; put every submit button back to normal.
  window.addEventListener("pageshow", () => {
    document.querySelectorAll("form.js-validate").forEach((form) => {
      delete form.dataset.sending;
      const btn = form.querySelector("[type=submit]");
      if (!btn || !btn.classList.contains("is-loading")) return;
      btn.classList.remove("is-loading");
      btn.removeAttribute("aria-busy");
      btn.removeAttribute("aria-disabled");
      const label = btn.querySelector(".btn__label");
      if (label && btn.dataset.label) label.textContent = btn.dataset.label;
    });
  });

  /* ----------------------------------------------------------- validation */
  const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  document.querySelectorAll("form.js-validate").forEach((form) => {
    form.addEventListener("submit", (e) => {
      let firstInvalid = null;
      form.querySelectorAll("[required]").forEach((field) => {
        const empty = field.type === "file" ? !field.files || !field.files.length : !field.value || !field.value.trim();
        field.classList.toggle("is-invalid", empty);
        if (empty && !firstInvalid) firstInvalid = field;
      });
      form.querySelectorAll('input[type="email"]').forEach((field) => {
        if (field.value && !emailRe.test(field.value.trim())) {
          field.classList.add("is-invalid");
          if (!firstInvalid) firstInvalid = field;
        }
      });
      const file = form.querySelector('input[type="file"]');
      if (file && file.files && file.files[0]) {
        const f = file.files[0];
        const bad = !/\.(pdf|docx?|pptx?)$/i.test(f.name) || f.size > 10 * 1024 * 1024;
        file.classList.toggle("is-invalid", bad);
        if (bad && !firstInvalid) firstInvalid = file;
      }
      if (firstInvalid) {
        e.preventDefault();
        if (firstInvalid.type !== "file") firstInvalid.focus();
        else firstInvalid.closest(".dropzone").scrollIntoView({ block: "center" });
      } else {
        // Valid: spin until the server answers with the success panel.
        // Block a second click, which would send a duplicate enquiry.
        if (form.dataset.sending) {
          e.preventDefault();
          return;
        }
        form.dataset.sending = "1";
        const btn = form.querySelector("[type=submit]");
        if (btn) {
          const label = btn.querySelector(".btn__label");
          if (label) {
            btn.dataset.label = label.textContent;
            label.textContent = "Sending";
          }
          btn.classList.add("is-loading");
          btn.setAttribute("aria-busy", "true");
          btn.setAttribute("aria-disabled", "true");
        }
      }
    });
    form.querySelectorAll("input, textarea, select").forEach((field) => {
      field.addEventListener("input", () => field.classList.remove("is-invalid"));
      field.addEventListener("change", () => field.classList.remove("is-invalid"));
    });
  });

  /* ------------------------------------------------------------- dropzone */
  document.querySelectorAll(".dropzone").forEach((zone) => {
    const input = zone.querySelector("input[type=file]");
    const nameEl = zone.querySelector("[data-dropzone-name]");
    if (!input || !nameEl) return;
    const original = nameEl.textContent;
    const update = () => {
      nameEl.textContent = input.files && input.files[0] ? input.files[0].name : original;
    };
    input.addEventListener("change", update);
    ["dragenter", "dragover"].forEach((ev) => zone.addEventListener(ev, () => zone.classList.add("is-drag")));
    ["dragleave", "drop"].forEach((ev) => zone.addEventListener(ev, () => zone.classList.remove("is-drag")));
    input.addEventListener("drop", () => window.setTimeout(update, 0));
  });
})();
