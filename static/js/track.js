/* Visitor tracking — times how long each interactive module is on screen and
   beacons the totals to POST /t when the page is hidden or left. Page views
   themselves are recorded server-side, so this only adds module dwell time. */
(function () {
  if (!("IntersectionObserver" in window) || !navigator.sendBeacon) return;

  var MODULES = [
    ["#hero", "Hero"],
    ["#region-map", "Regional Map"],
    ["#getting-there", "Getting There"],
    ["#itinerary", "Itinerary"],
    ["#estimator", "Estimator"],
    ["#island-intro", "Island Detail"],
  ];
  var MIN_MS = 2000; // ignore modules merely scrolled past

  var tracked = [];
  MODULES.forEach(function (m) {
    var el = document.querySelector(m[0]);
    if (el) tracked.push({ el: el, module: m[1], ms: 0, since: null });
  });
  if (!tracked.length) return;

  function start(t) { if (t.since === null && !document.hidden) t.since = performance.now(); }
  function stop(t) { if (t.since !== null) { t.ms += performance.now() - t.since; t.since = null; } }

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      var t = tracked.find(function (x) { return x.el === entry.target; });
      if (!t) return;
      t.visible = entry.isIntersecting;
      entry.isIntersecting ? start(t) : stop(t);
    });
  }, { threshold: 0.35 });
  tracked.forEach(function (t) { io.observe(t.el); });

  function flush() {
    var modules = [];
    tracked.forEach(function (t) {
      stop(t);
      if (t.ms >= MIN_MS) modules.push({ module: t.module, ms: Math.round(t.ms) });
      t.ms = 0;
    });
    if (modules.length) {
      var body = new Blob([JSON.stringify({ path: location.pathname, modules: modules })], { type: "application/json" });
      navigator.sendBeacon("/t", body);
    }
  }

  document.addEventListener("visibilitychange", function () {
    if (document.hidden) flush();
    else tracked.forEach(function (t) { if (t.visible) start(t); });
  });
  window.addEventListener("pagehide", flush);
})();
