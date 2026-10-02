/* Home-page premium layer — 3D depth and cinematic transitions.
   Purely additive: every effect checks its elements/libraries exist, fine-pointer
   effects skip touch devices, and prefers-reduced-motion turns the motion off. */
(() => {
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));

  /* ------------------------------------------------ scroll progress line */
  const bar = document.createElement("div");
  bar.className = "scroll-progress";
  bar.setAttribute("aria-hidden", "true");
  document.body.appendChild(bar);
  let barRaf = null;
  const syncBar = () => {
    barRaf = null;
    const max = document.documentElement.scrollHeight - window.innerHeight;
    bar.style.transform = `scaleX(${max > 0 ? clamp(window.scrollY / max, 0, 1) : 0})`;
  };
  window.addEventListener("scroll", () => { if (!barRaf) barRaf = requestAnimationFrame(syncBar); }, { passive: true });
  syncBar();

  if (reduce) return;

  /* ------------------------------------------- hero: spotlight + depth */
  const hero = document.getElementById("hero");
  if (hero && finePointer) {
    const spot = document.createElement("div");
    spot.className = "hero__spot";
    spot.setAttribute("aria-hidden", "true");
    hero.appendChild(spot);
    const title = hero.querySelector(".hero__title");
    let raf = null;
    hero.addEventListener("pointermove", (e) => {
      if (raf) cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const r = hero.getBoundingClientRect();
        const x = (e.clientX - r.left) / r.width;
        const y = (e.clientY - r.top) / r.height;
        hero.style.setProperty("--mx", `${(x * 100).toFixed(1)}%`);
        hero.style.setProperty("--my", `${(y * 100).toFixed(1)}%`);
        if (title) title.style.translate = `${((0.5 - x) * 26).toFixed(1)}px ${((0.5 - y) * 16).toFixed(1)}px`;
      });
    });
    hero.addEventListener("pointerenter", () => hero.classList.add("is-lit"));
    hero.addEventListener("pointerleave", () => {
      hero.classList.remove("is-lit");
      if (title) title.style.translate = "";
    });
  }

  /* ------------------------------------ island rail: coverflow + 3D tilt */
  const viewport = document.querySelector(".islands-rail [data-carousel-viewport]");
  const cards = viewport ? Array.from(viewport.querySelectorAll(".rail-card")) : [];
  if (viewport && cards.length) {
    let flowRaf = null;
    const flow = () => {
      flowRaf = null;
      const vr = viewport.getBoundingClientRect();
      const mid = vr.left + vr.width / 2;
      cards.forEach((card) => {
        const cr = card.getBoundingClientRect();
        const d = clamp((cr.left + cr.width / 2 - mid) / vr.width, -1, 1);
        card.style.setProperty("--flow", `${(-d * 9).toFixed(2)}deg`);
        card.style.setProperty("--fs", (1 - Math.abs(d) * 0.05).toFixed(3));
      });
    };
    const queueFlow = () => { if (!flowRaf) flowRaf = requestAnimationFrame(flow); };
    viewport.addEventListener("scroll", queueFlow, { passive: true });
    window.addEventListener("resize", queueFlow);
    flow();

    if (finePointer) {
      cards.forEach((card) => {
        card.addEventListener("pointermove", (e) => {
          const r = card.getBoundingClientRect();
          const x = (e.clientX - r.left) / r.width;
          const y = (e.clientY - r.top) / r.height;
          card.style.setProperty("--ry", `${((x - 0.5) * 12).toFixed(2)}deg`);
          card.style.setProperty("--rx", `${((0.5 - y) * 10).toFixed(2)}deg`);
          card.style.setProperty("--gx", `${(x * 100).toFixed(1)}%`);
          card.style.setProperty("--gy", `${(y * 100).toFixed(1)}%`);
          card.classList.add("is-tilt");
        });
        card.addEventListener("pointerleave", () => {
          card.classList.remove("is-tilt");
          card.style.setProperty("--ry", "0deg");
          card.style.setProperty("--rx", "0deg");
        });
      });
    }
  }

  /* ---------------------------------------------- GSAP scroll scenes */
  const { gsap, ScrollTrigger } = window;
  if (gsap && ScrollTrigger) {
    gsap.registerPlugin(ScrollTrigger);

    // Island cards swing in from depth, one after another.
    if (cards.length) {
      gsap.from(cards, {
        rotateY: -32, x: 140, opacity: 0, transformPerspective: 1200, transformOrigin: "0% 50%",
        duration: 1.4, ease: "expo.out", stagger: 0.08, clearProps: "transform,opacity",
        scrollTrigger: { trigger: viewport, start: "top 82%", once: true },
      });
    }

    // Full-bleed bands open from a rounded, inset frame to full width.
    document.querySelectorAll(".page-home .wwd, .page-home .possible").forEach((band) => {
      gsap.fromTo(band,
        { clipPath: "inset(6% 5% 0% 5% round 28px)" },
        { clipPath: "inset(0% 0% 0% 0% round 0px)", ease: "none",
          scrollTrigger: { trigger: band, start: "top 96%", end: "top 30%", scrub: 0.6 } });
    });
  }
})();
