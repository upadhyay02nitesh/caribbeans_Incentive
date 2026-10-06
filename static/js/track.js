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

/* Precise location (optional enrichment). The server already stores an
   approximate IP location for every visitor; this asks the browser once for
   GPS and, only if the visitor allows it, sends the coordinates to
   POST /t/location. Never blocks the page and never asks twice: a timestamp in
   localStorage records that we asked, and a "denied" permission is respected. */
(function () {
  var KEY = "ci_geo_asked";
  var ASK_AFTER_MS = 8000;               // let the visitor see the page first
  var REASK_MS = 30 * 24 * 3600 * 1000;  // refresh a granted location at most monthly
  if (!window.isSecureContext || !("geolocation" in navigator) || !window.fetch) return;
  var asked = 0;
  try { asked = +localStorage.getItem(KEY) || 0; } catch (e) { return; } // can't remember -> don't risk re-prompting
  if (Date.now() - asked < REASK_MS) return;

  function remember() { try { localStorage.setItem(KEY, String(Date.now())); } catch (e) {} }
  function send(pos) {
    fetch("/t/location", {
      method: "POST", credentials: "same-origin", keepalive: true,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ latitude: pos.coords.latitude, longitude: pos.coords.longitude, accuracy: pos.coords.accuracy })
    }).catch(function () {});
  }
  function ask() {
    remember();
    navigator.geolocation.getCurrentPosition(send, function () { /* denied / timeout / unavailable: IP location stands */ },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 10 * 60 * 1000 });
  }
  function decide(state) {
    if (state === "denied") { remember(); return; }
    window.setTimeout(ask, state === "granted" ? 0 : ASK_AFTER_MS);
  }
  if (navigator.permissions && navigator.permissions.query) {
    navigator.permissions.query({ name: "geolocation" }).then(function (s) { decide(s.state); }, function () { decide("prompt"); });
  } else {
    decide("prompt");
  }
})();
