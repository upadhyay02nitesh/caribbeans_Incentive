/* MODULE 3 — Island detail: sticky sub-nav scroll-spy + expanding cards. */
(() => {
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ------------------------------------------------------------ sub-nav */
  const subnav = document.getElementById("island-subnav");
  const links = Array.from(document.querySelectorAll(".island-subnav__link"));
  const panels = links.map((l) => document.getElementById(l.dataset.target)).filter(Boolean);

  const setActive = (id) => links.forEach((l) => l.classList.toggle("is-active", l.dataset.target === id));

  links.forEach((link) => {
    link.addEventListener("click", (e) => {
      const target = document.getElementById(link.dataset.target);
      if (!target) return;
      e.preventDefault();
      const offset = -((subnav ? subnav.offsetHeight : 0) + 10);
      if (window.CI && window.CI.scrollTo) window.CI.scrollTo(target, offset);
      else window.scrollTo({ top: target.getBoundingClientRect().top + window.scrollY + offset, behavior: reduce ? "auto" : "smooth" });
      setActive(link.dataset.target);
      history.replaceState(null, "", `#${link.dataset.target}`);
    });
  });

  if (panels.length && "IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) setActive(entry.target.id);
        });
      },
      { rootMargin: "-40% 0px -55% 0px", threshold: 0 }
    );
    panels.forEach((p) => observer.observe(p));
  }

  /* ----------------------------------------------------- expanding cards */
  const measure = (card) => {
    const body = card.querySelector(".expand-card__body");
    if (body) card.style.setProperty("--body-h", `${body.offsetHeight}px`);
  };

  document.querySelectorAll(".expand-cards").forEach((group) => {
    const cards = Array.from(group.querySelectorAll(".expand-card"));
    const open = (card) => {
      cards.forEach((c) => {
        const on = c === card;
        c.classList.toggle("is-open", on);
        c.querySelector(".expand-card__head").setAttribute("aria-expanded", on ? "true" : "false");
      });
      if (card) {
        // Measure after the flex width settles so the title lifts the right amount.
        measure(card);
        window.setTimeout(() => measure(card), reduce ? 0 : 950);
      }
    };

    cards.forEach((card) => {
      const head = card.querySelector(".expand-card__head");
      head.addEventListener("click", () => open(card.classList.contains("is-open") ? null : card));
    });

    // First card starts open so each row reads as a composed spread.
    if (cards[0]) open(cards[0]);
  });

  window.addEventListener("resize", () => {
    document.querySelectorAll(".expand-card.is-open").forEach(measure);
  });
})();
