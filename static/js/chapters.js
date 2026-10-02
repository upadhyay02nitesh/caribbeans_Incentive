/* Your Caribbean Journey: chapter index scroll-spy. */
(() => {
  const links = Array.from(document.querySelectorAll("[data-chapter-link]"));
  const chapters = Array.from(document.querySelectorAll("[data-chapter]"));
  if (!links.length || !chapters.length || !("IntersectionObserver" in window)) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        links.forEach((l) => l.classList.toggle("is-active", l.dataset.chapterLink === entry.target.id));
      });
    },
    { rootMargin: "-35% 0px -60% 0px" }
  );
  chapters.forEach((c) => observer.observe(c));
})();
