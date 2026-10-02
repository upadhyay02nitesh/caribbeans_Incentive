/* Caribbean Incentive — motion engine.
   Order matters: text is split first, THEN html.reveal-init is added (which is
   what hides pending elements), THEN observers start. If this file never runs,
   nothing is ever hidden. GSAP / Lenis are optional enhancements: every effect
   that needs them checks for them first. */
(() => {
  const html = document.documentElement;
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  const hasGsap = !!(window.gsap && window.ScrollTrigger);
  const CI = (window.CI = window.CI || {});

  /* ---------------------------------------------------------------- split */
  const wrapWords = (root, makeWord) => {
    let index = 0;
    const walk = (node) => {
      Array.from(node.childNodes).forEach((child) => {
        if (child.nodeType === Node.TEXT_NODE) {
          const parts = child.textContent.split(/(\s+)/);
          if (parts.length === 1 && !parts[0]) return;
          const frag = document.createDocumentFragment();
          parts.forEach((part) => {
            if (!part) return;
            if (/^\s+$/.test(part)) frag.appendChild(document.createTextNode(" "));
            else frag.appendChild(makeWord(part, index++));
          });
          node.replaceChild(frag, child);
        } else if (child.nodeType === Node.ELEMENT_NODE) {
          walk(child);
        }
      });
    };
    walk(root);
  };

  document.querySelectorAll("[data-split]").forEach((el) => {
    if (el.dataset.splitDone) return;
    el.dataset.splitDone = "1";
    el.setAttribute("aria-label", el.textContent.trim().replace(/\s+/g, " "));
    wrapWords(el, (word, i) => {
      const outer = document.createElement("span");
      outer.className = "sw";
      outer.setAttribute("aria-hidden", "true");
      const inner = document.createElement("span");
      inner.className = "sw__i";
      inner.style.setProperty("--wi", i);
      inner.textContent = word;
      outer.appendChild(inner);
      return outer;
    });
  });

  if (hasGsap && !reduce) {
    document.querySelectorAll("[data-lit]").forEach((el) => {
      wrapWords(el, (word) => {
        const s = document.createElement("span");
        s.className = "lw";
        s.textContent = word;
        return s;
      });
    });
  }

  /* --------------------------------------------------------------- reveal */
  html.classList.add("reveal-init");
  const revealEls = document.querySelectorAll("[data-reveal], .reveal, [data-split], [data-clip]");
  if (reduce || !("IntersectionObserver" in window)) {
    revealEls.forEach((el) => el.classList.add("is-in"));
  } else {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-in");
          io.unobserve(entry.target);
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -6% 0px" }
    );
    // A clip-path of inset(100%) makes the element itself count as fully
    // clipped, so clipped media are observed through their parent instead.
    const proxies = new Map();
    revealEls.forEach((el) => {
      if (el.hasAttribute("data-clip") && el.parentElement) {
        const parent = el.parentElement;
        if (!proxies.has(parent)) proxies.set(parent, []);
        proxies.get(parent).push(el);
      } else {
        io.observe(el);
      }
    });
    const pio = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          (proxies.get(entry.target) || []).forEach((el) => el.classList.add("is-in"));
          pio.unobserve(entry.target);
        });
      },
      { threshold: 0.08, rootMargin: "0px 0px -6% 0px" }
    );
    proxies.forEach((_, parent) => pio.observe(parent));
    // Safety net: anything still pending after a long idle is shown.
    window.addEventListener("load", () => {
      window.setTimeout(() => {
        revealEls.forEach((el) => {
          const r = el.getBoundingClientRect();
          if (r.top < window.innerHeight && r.bottom > 0) el.classList.add("is-in");
        });
      }, 2500);
    });
  }

  /* ---------------------------------------------------------- smooth scroll */
  let lenis = null;
  if (window.Lenis && !reduce) {
    lenis = new window.Lenis({ lerp: 0.09, wheelMultiplier: 1, smoothWheel: true });
    html.classList.add("lenis");
    if (hasGsap) {
      lenis.on("scroll", window.ScrollTrigger.update);
      window.gsap.ticker.add((t) => lenis.raf(t * 1000));
      window.gsap.ticker.lagSmoothing(0);
    } else {
      const raf = (t) => {
        lenis.raf(t);
        requestAnimationFrame(raf);
      };
      requestAnimationFrame(raf);
    }
  }
  CI.lenis = lenis;
  CI.scrollTo = (target, offset = 0) => {
    const el = typeof target === "string" ? document.querySelector(target) : target;
    if (target !== 0 && !el) return;
    if (lenis) {
      lenis.scrollTo(target === 0 ? 0 : el, { offset, duration: 1.4 });
    } else {
      const top = target === 0 ? 0 : el.getBoundingClientRect().top + window.scrollY + offset;
      window.scrollTo({ top, behavior: reduce ? "auto" : "smooth" });
    }
  };

  document.addEventListener("click", (e) => {
    const link = e.target.closest("[data-scroll-to], [data-scroll-top]");
    if (!link) return;
    if (link.hasAttribute("data-scroll-top")) {
      e.preventDefault();
      CI.scrollTo(0);
      return;
    }
    const hash = link.getAttribute("href");
    if (!hash || hash.charAt(0) !== "#" || hash.length < 2) return;
    const target = document.querySelector(hash);
    if (!target) return;
    e.preventDefault();
    CI.scrollTo(target, -90);
    history.replaceState(null, "", hash);
  });

  /* ------------------------------------------------------------ magnetic */
  if (finePointer && !reduce) {
    document.querySelectorAll("[data-magnetic]").forEach((el) => {
      const strength = 0.28;
      el.addEventListener("pointermove", (e) => {
        const r = el.getBoundingClientRect();
        const x = (e.clientX - r.left - r.width / 2) * strength;
        const y = (e.clientY - r.top - r.height / 2) * strength * 1.2;
        el.style.transform = `translate3d(${x}px, ${y}px, 0)`;
      });
      el.addEventListener("pointerleave", () => {
        el.style.transform = "";
      });
    });
  }

  /* ------------------------------------------------- hover image preview */
  document.querySelectorAll("[data-hover-reveal]").forEach((section) => {
    const float = section.querySelector(".hover-float");
    const img = float && float.querySelector("img");
    if (!float || !img || !finePointer || reduce) return;
    let x = 0, y = 0, cx = 0, cy = 0, running = false;
    const loop = () => {
      cx += (x - cx) * 0.14;
      cy += (y - cy) * 0.14;
      float.style.translate = `${cx - float.offsetWidth / 2}px ${cy - float.offsetHeight / 2}px`;
      if (running) requestAnimationFrame(loop);
    };
    section.querySelectorAll("[data-hover-img]").forEach((row) => {
      row.addEventListener("pointerenter", (e) => {
        img.src = row.dataset.hoverImg;
        if (!running) {
          cx = x = e.clientX;
          cy = y = e.clientY;
          running = true;
          requestAnimationFrame(loop);
        }
        float.classList.add("is-active");
      });
      row.addEventListener("pointerleave", () => float.classList.remove("is-active"));
    });
    section.addEventListener("pointermove", (e) => {
      x = e.clientX;
      y = e.clientY;
    });
    section.addEventListener("pointerleave", () => {
      running = false;
      float.classList.remove("is-active");
    });
  });

  /* ------------------------------------------------------------ counters */
  const counters = document.querySelectorAll("[data-count]");
  if (counters.length && !reduce && "IntersectionObserver" in window) {
    const cio = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          cio.unobserve(entry.target);
          const el = entry.target;
          const to = Number(el.dataset.count);
          // Counters in a row fire one after another, not all at once.
          const delay = Number(el.dataset.countDelay) || 0;
          const start = performance.now() + delay;
          const dur = 1400;
          const tick = (now) => {
            const p = Math.min(Math.max((now - start) / dur, 0), 1);
            const eased = 1 - Math.pow(1 - p, 4);
            el.textContent = String(Math.round(to * eased)).padStart(2, "0");
            if (p < 1) requestAnimationFrame(tick);
          };
          el.textContent = "00";
          requestAnimationFrame(tick);
        });
      },
      { threshold: 0.6 }
    );
    counters.forEach((el) => cio.observe(el));
  }

  /* ------------------------------------------------ horizontal rails (native) */
  document.querySelectorAll("[data-hscroll]").forEach((viewport) => {
    const section = viewport.closest("section");
    const bar = section && section.querySelector("[data-hscroll-progress]");
    if (!bar) return;
    viewport.addEventListener(
      "scroll",
      () => {
        if (viewport.classList.contains("is-pinned")) return;
        const max = viewport.scrollWidth - viewport.clientWidth;
        bar.style.transform = `scaleX(${max > 0 ? viewport.scrollLeft / max : 0})`;
      },
      { passive: true }
    );
  });

  /* ----------------------------------------------------------- 3D tilt */
  // Pointer-driven parallax tilt on stacked media. Fine pointers only.
  if (finePointer && !reduce) {
    document.querySelectorAll("[data-tilt]").forEach((stage) => {
      const shots = stage.querySelectorAll(".intro__shot");
      if (!shots.length) return;
      let raf = null;
      const move = (e) => {
        const r = stage.getBoundingClientRect();
        const x = (e.clientX - r.left) / r.width - 0.5;
        const y = (e.clientY - r.top) / r.height - 0.5;
        if (raf) cancelAnimationFrame(raf);
        raf = requestAnimationFrame(() => {
          const depths = [1, -1.4];
          const lifts = [0, 40];
          shots.forEach((shot, i) => {
            const depth = depths[i] !== undefined ? depths[i] : 1;
            const lift = lifts[i] !== undefined ? lifts[i] : 0;
            shot.style.transform =
              `rotateY(${(x * 9 * depth).toFixed(2)}deg) rotateX(${(-y * 7 * depth).toFixed(2)}deg) translateZ(${lift}px)`;
          });
        });
      };
      stage.addEventListener("pointerenter", () => stage.classList.add("is-tilting"));
      stage.addEventListener("pointermove", move);
      stage.addEventListener("pointerleave", () => {
        stage.classList.remove("is-tilting");
        shots.forEach((shot) => (shot.style.transform = ""));
      });
    });
  }

  /* ------------------------------------------------------ arrow carousels */
  document.querySelectorAll("[data-carousel]").forEach((root) => {
    const viewport = root.querySelector("[data-carousel-viewport]");
    const prev = root.querySelector("[data-carousel-prev]");
    const next = root.querySelector("[data-carousel-next]");
    if (!viewport) return;
    const step = () => {
      const track = viewport.firstElementChild;
      const card = track && track.firstElementChild;
      if (!card) return viewport.clientWidth * 0.8;
      const gap = parseFloat(getComputedStyle(track).columnGap) || 0;
      return card.getBoundingClientRect().width + gap;
    };
    const sync = () => {
      const max = viewport.scrollWidth - viewport.clientWidth - 2;
      if (prev) prev.disabled = viewport.scrollLeft <= 2;
      if (next) next.disabled = viewport.scrollLeft >= max;
    };
    const go = (dir) => viewport.scrollBy({ left: dir * step(), behavior: reduce ? "auto" : "smooth" });
    if (prev) prev.addEventListener("click", () => go(-1));
    if (next) next.addEventListener("click", () => go(1));
    viewport.addEventListener("scroll", sync, { passive: true });
    window.addEventListener("resize", sync);
    sync();
  });

  /* ------------------------------------------------------ GSAP scroll scenes */
  if (!hasGsap || reduce) return;
  const { gsap, ScrollTrigger } = window;
  gsap.registerPlugin(ScrollTrigger);

  // Scroll-lit statements: words brighten as they cross the viewport.
  document.querySelectorAll("[data-lit]").forEach((el) => {
    const words = el.querySelectorAll(".lw");
    if (!words.length) return;
    gsap.fromTo(
      words,
      { opacity: 0.14 },
      {
        opacity: 1,
        ease: "none",
        stagger: 0.08,
        scrollTrigger: { trigger: el, start: "top 88%", end: "bottom 50%", scrub: 0.6 },
      }
    );
  });

  // Parallax media (value = travel in yPercent).
  document.querySelectorAll("[data-parallax]").forEach((el) => {
    const amount = Number(el.dataset.parallax) || 8;
    gsap.fromTo(
      el,
      { yPercent: -amount },
      {
        yPercent: amount,
        ease: "none",
        scrollTrigger: { trigger: el.parentElement, start: "top bottom", end: "bottom top", scrub: true },
      }
    );
  });

  // Hero media drifts slower than the page (inner-page heroes).
  document.querySelectorAll("[data-page-hero], .hero, .connect__intro, .lost").forEach((hero) => {
    const media = hero.querySelector(".page-hero__media, .island-hero__media, .hero__media, .connect__bg, .lost__bg");
    const content = hero.querySelector(".page-hero__content, .island-hero__content, .hero__content");
    if (media) {
      gsap.to(media, { yPercent: 22, ease: "none", scrollTrigger: { trigger: hero, start: "top top", end: "bottom top", scrub: true } });
    }
    if (content) {
      gsap.to(content, { yPercent: -18, opacity: 0.2, ease: "none", scrollTrigger: { trigger: hero, start: "top top", end: "bottom top", scrub: true } });
    }
  });

  const mm = gsap.matchMedia();

  mm.add("(min-width: 992px)", () => {
    // Welcome circle columns drift up / down against each other.
    document.querySelectorAll("[data-drift]").forEach((col) => {
      const amount = Number(col.dataset.drift) || 10;
      gsap.fromTo(
        col,
        { yPercent: -amount / 2 },
        {
          yPercent: amount / 2,
          ease: "none",
          scrollTrigger: { trigger: col.parentElement, start: "top bottom", end: "bottom top", scrub: 0.6 },
        }
      );
    });

    // Pinned horizontal rails.
    document.querySelectorAll("[data-hscroll]").forEach((viewport) => {
      const track = viewport.querySelector("[data-hscroll-track]");
      if (!track) return;
      const pinEl = viewport.closest(".hjourney__pin, .islands-rail__stage") || viewport;
      const section = viewport.closest("section");
      const bar = section && section.querySelector("[data-hscroll-progress]");
      viewport.classList.add("is-pinned");
      const distance = () => {
        const pad = parseFloat(getComputedStyle(viewport).paddingLeft) || 0;
        return Math.max(0, track.scrollWidth - (viewport.clientWidth - pad * 2));
      };
      const tween = gsap.to(track, {
        x: () => -distance(),
        ease: "none",
        scrollTrigger: {
          trigger: pinEl,
          start: "top top",
          end: () => `+=${distance()}`,
          pin: pinEl,
          scrub: 0.8,
          invalidateOnRefresh: true,
          onUpdate: (self) => {
            if (bar) bar.style.transform = `scaleX(${self.progress})`;
          },
        },
      });
      return () => {
        viewport.classList.remove("is-pinned");
        tween.kill();
        gsap.set(track, { clearProps: "transform" });
      };
    });

    // Expanding media scene.
    document.querySelectorAll("[data-expand]").forEach((section) => {
      const stage = section.querySelector(".expand__stage");
      const media = section.querySelector(".expand__media");
      const img = media && media.querySelector("img");
      const content = section.querySelector(".expand__content");
      if (!stage || !media) return;
      html.classList.add("has-expand");
      const tl = gsap.timeline({
        scrollTrigger: { trigger: stage, start: "top top", end: "+=110%", pin: true, scrub: 0.8 },
      });
      tl.fromTo(media, { clipPath: "inset(16% 22% 16% 22% round 22px)" }, { clipPath: "inset(0% 0% 0% 0% round 0px)", ease: "power2.inOut", duration: 1 }, 0)
        .fromTo(img, { scale: 1.35 }, { scale: 1, ease: "power2.inOut", duration: 1 }, 0)
        .fromTo(content.children, { opacity: 0, y: 70 }, { opacity: 1, y: 0, stagger: 0.08, duration: 0.5, ease: "power3.out" }, 0.55);
      return () => tl.kill();
    });

    // Journey progress meter.
    document.querySelectorAll("[data-journey]").forEach((list) => {
      const meter = list.closest("section").querySelector("[data-journey-meter]");
      if (!meter) return;
      gsap.fromTo(meter, { scaleY: 0 }, { scaleY: 1, ease: "none", scrollTrigger: { trigger: list, start: "top 60%", end: "bottom 60%", scrub: true } });
    });
  });

  window.addEventListener("load", () => ScrollTrigger.refresh());
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => ScrollTrigger.refresh());
})();
