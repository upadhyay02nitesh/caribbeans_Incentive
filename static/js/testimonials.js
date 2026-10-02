/* Testimonial carousel: crossfading quotes, numbered controls, pauses on hover/focus. */
(() => {
  const root = document.getElementById("testimonial-carousel");
  if (!root) return;

  const slides = Array.from(root.querySelectorAll(".testimonial-slide"));
  const dots = Array.from(root.querySelectorAll(".testimonial-dot"));
  if (slides.length < 2) return;

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let current = 0;
  let timer = null;

  const show = (index) => {
    slides[current].classList.remove("is-active");
    slides[current].setAttribute("aria-hidden", "true");
    dots[current].classList.remove("is-active");
    dots[current].setAttribute("aria-selected", "false");
    current = index;
    slides[current].classList.add("is-active");
    slides[current].removeAttribute("aria-hidden");
    dots[current].classList.add("is-active");
    dots[current].setAttribute("aria-selected", "true");
  };

  const next = () => show((current + 1) % slides.length);
  const stop = () => {
    if (timer) window.clearInterval(timer);
    timer = null;
  };
  const start = () => {
    if (reduceMotion) return;
    stop();
    timer = window.setInterval(next, 8000);
  };

  dots.forEach((dot, i) => {
    dot.addEventListener("click", () => {
      show(i);
      start();
    });
  });

  root.addEventListener("mouseenter", stop);
  root.addEventListener("mouseleave", start);
  root.addEventListener("focusin", stop);
  root.addEventListener("focusout", start);

  start();
})();
