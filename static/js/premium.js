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

  if (reduce) { drawWaveOnce(); return; }

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

  /* ------------------------------------------ 3D ocean wave particle field */
  startWave();

  function makeWave() {
    const host = document.querySelector(".page-home .map-section");
    if (!host) return null;
    const canvas = document.createElement("canvas");
    canvas.className = "wave-field";
    canvas.setAttribute("aria-hidden", "true");
    host.prepend(canvas);
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;

    const COLS = 72, ROWS = 26;
    const light = host.classList.contains("map-section--light");
    const pointer = { x: -9999, y: -9999 };
    let w = 0, h = 0, dpr = 1;

    const resize = () => {
      dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      w = canvas.clientWidth; h = canvas.clientHeight;
      canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    host.addEventListener("pointermove", (e) => {
      const r = canvas.getBoundingClientRect();
      pointer.x = e.clientX - r.left; pointer.y = e.clientY - r.top;
    });
    host.addEventListener("pointerleave", () => { pointer.x = pointer.y = -9999; });

    const draw = (t) => {
      ctx.clearRect(0, 0, w, h);
      for (let r = 0; r < ROWS; r++) {
        const z = r / (ROWS - 1);                 // 0 = horizon, 1 = nearest row
        const persp = 0.28 + z * z * 0.9;          // rows spread as they approach
        for (let c = 0; c < COLS; c++) {
          const u = c / (COLS - 1) - 0.5;
          const swell = Math.sin(u * 7 + t * 0.00055 + z * 5) * 0.6
                      + Math.sin(u * 13 - t * 0.0009 + z * 9) * 0.25
                      + Math.cos(z * 7 - t * 0.0007) * 0.35;
          let x = w / 2 + u * w * 1.35 * persp;
          let y = h * 0.1 + Math.pow(z, 1.35) * h * 0.86 - swell * 16 * persp;
          const dx = x - pointer.x, dy = y - pointer.y;
          const near = Math.exp(-(dx * dx + dy * dy) / 9000);   // ripple around the cursor
          y -= near * 22 * persp;
          const size = 0.5 + z * 1.7 + near * 1.4;
          const crest = clamp((swell + 1.2) / 2.4, 0, 1);
          const alpha = (0.08 + z * 0.5) * (0.55 + crest * 0.45);
          // Troughs in lagoon teal, crests warming to champagne gold (deeper tones on the light map section).
          const cr = light ? Math.round(31 + crest * 153) : Math.round(90 + crest * 150);
          const cg = light ? Math.round(140 - crest * 10) : Math.round(200 - crest * 20);
          const cb = light ? Math.round(135 - crest * 88) : Math.round(200 - crest * 90);
          ctx.fillStyle = `rgba(${cr},${cg},${cb},${alpha.toFixed(3)})`;
          ctx.beginPath(); ctx.arc(x, y, size, 0, Math.PI * 2); ctx.fill();
        }
      }
    };
    resize();
    window.addEventListener("resize", resize);
    return { canvas, draw };
  }

  function startWave() {
    const wave = makeWave();
    if (!wave) return;
    let running = false, raf = null;
    const loop = (t) => { wave.draw(t); raf = requestAnimationFrame(loop); };
    new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting && !running) { running = true; raf = requestAnimationFrame(loop); }
      else if (!entry.isIntersecting && running) { running = false; cancelAnimationFrame(raf); }
    }).observe(wave.canvas);
  }

  function drawWaveOnce() {
    const wave = makeWave();
    if (wave) wave.draw(0);
  }
})();
