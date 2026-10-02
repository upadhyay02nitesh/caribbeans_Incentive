"""Live visitor tracking for the admin's Visitors, Dashboard and Analytics pages.

Storage is deliberately compact — no per-click history is kept:

    caribbean_incentive_visitors      one row per browser (cookie `ci_vid`), with
                                      running totals: sessions, pages, time per
                                      module, last page, whether they opened Connect
    caribbean_incentive_daily_stats   one row per day: sessions, page views,
                                      bounces, session time, sessions per hour,
                                      module hits/time, island page views

So the database grows by one row per visitor plus one row per day, however
busy the site gets.

How it is fed:
  * every public HTML page view is recorded server-side (`after_app_request`
    in routes/track.py), so tracking works even with JavaScript off;
  * static/js/track.js beacons how long each interactive module was on screen
    to POST /t, which ranks "Top module";
  * a gap of 30+ minutes since `last_seen` starts a new session;
  * submitting a brief, RFP or callback stamps the visitor with that name,
    email and company, and marks them Converted.

City/country come from a one-off IP lookup (GEOIP_URL) when a visitor is first
seen. Writes go through a background queue so a slow database never slows a
page down, and everything is skipped when DATABASE_URL is not configured.
"""

import json
import logging
import queue
import re
import secrets
import threading
import urllib.request
from datetime import datetime, timedelta, timezone
from ipaddress import ip_address
from urllib.parse import urlparse

from flask import current_app, request

from services.runtime import SERVERLESS
from services.store import PREFIX, _connect, _dsn

logger = logging.getLogger(__name__)

VISITORS = f"{PREFIX}_visitors"
DAILY = f"{PREFIX}_daily_stats"
LEGACY_EVENTS = f"{PREFIX}_visitor_events"  # per-click history, no longer kept

COOKIE = "ci_vid"
COOKIE_MAX_AGE = 60 * 60 * 24 * 365
SESSION_GAP = timedelta(minutes=30)
ISLAND_PREFIX = "/explore-our-islands/"
CONNECT_PATH = "/lets-connect"

# Names track.js may report; anything else posted to /t is ignored.
MODULES = {"Hero", "Regional Map", "Getting There", "Itinerary", "Estimator", "Island Detail"}

SCHEMA = f"""
CREATE TABLE IF NOT EXISTS {VISITORS} (
    id                  BIGSERIAL PRIMARY KEY,
    visitor_key         TEXT UNIQUE NOT NULL,
    company             TEXT,
    name                TEXT,
    email               TEXT,
    city                TEXT,
    region              TEXT,
    country             TEXT,
    network             TEXT,
    ip                  TEXT,
    source              TEXT,
    referrer            TEXT,
    landing_page        TEXT,
    device              TEXT,
    browser             TEXT,
    os                  TEXT,
    user_agent          TEXT,
    sessions            INTEGER NOT NULL DEFAULT 1,
    pages_viewed        INTEGER NOT NULL DEFAULT 0,
    converted_kind      TEXT,
    converted_reference TEXT,
    first_seen          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE {VISITORS} ADD COLUMN IF NOT EXISTS last_page       TEXT;
ALTER TABLE {VISITORS} ADD COLUMN IF NOT EXISTS last_title      TEXT;
ALTER TABLE {VISITORS} ADD COLUMN IF NOT EXISTS module_ms       JSONB NOT NULL DEFAULT '{{}}';
ALTER TABLE {VISITORS} ADD COLUMN IF NOT EXISTS saw_connect     BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE {VISITORS} ADD COLUMN IF NOT EXISTS session_started TIMESTAMPTZ;
ALTER TABLE {VISITORS} ADD COLUMN IF NOT EXISTS session_pages   INTEGER NOT NULL DEFAULT 1;
CREATE INDEX IF NOT EXISTS {VISITORS}_last_seen_idx ON {VISITORS} (last_seen DESC);

CREATE TABLE IF NOT EXISTS {DAILY} (
    day             DATE PRIMARY KEY,
    sessions        INTEGER NOT NULL DEFAULT 0,
    pageviews       INTEGER NOT NULL DEFAULT 0,
    bounces         INTEGER NOT NULL DEFAULT 0,
    session_seconds BIGINT  NOT NULL DEFAULT 0,
    hours           JSONB   NOT NULL DEFAULT '{{}}',   -- {{"14": sessions started at 14:00}}
    module_hits     JSONB   NOT NULL DEFAULT '{{}}',   -- {{"Estimator": engagements}}
    module_ms       JSONB   NOT NULL DEFAULT '{{}}',   -- {{"Estimator": total ms in view}}
    island_views    JSONB   NOT NULL DEFAULT '{{}}'    -- {{"st-barth": page views}}
);

-- Adds two {{key: number}} objects key by key (used to merge daily counters).
CREATE OR REPLACE FUNCTION {PREFIX}_jsonb_add(a JSONB, b JSONB) RETURNS JSONB
LANGUAGE sql IMMUTABLE AS $$
  SELECT COALESCE(jsonb_object_agg(k, COALESCE((a->>k)::numeric, 0) + COALESCE((b->>k)::numeric, 0)), '{{}}'::jsonb)
  FROM (SELECT jsonb_object_keys(COALESCE(a, '{{}}')) AS k
        UNION SELECT jsonb_object_keys(COALESCE(b, '{{}}'))) keys
$$;

-- One-off: fold the old per-click history into the visitor totals, then drop it.
DO $$ BEGIN
  IF to_regclass('{LEGACY_EVENTS}') IS NOT NULL THEN
    UPDATE {VISITORS} v SET
      module_ms = COALESCE((SELECT jsonb_object_agg(module, total) FROM (
                    SELECT module, SUM(duration_ms) AS total FROM {LEGACY_EVENTS} e
                    WHERE e.visitor_id = v.id AND e.kind = 'module' GROUP BY module) m), '{{}}'),
      last_page  = (SELECT path  FROM {LEGACY_EVENTS} e WHERE e.visitor_id = v.id AND e.kind = 'pageview' ORDER BY created_at DESC LIMIT 1),
      last_title = (SELECT title FROM {LEGACY_EVENTS} e WHERE e.visitor_id = v.id AND e.kind = 'pageview' ORDER BY created_at DESC LIMIT 1),
      saw_connect = EXISTS (SELECT 1 FROM {LEGACY_EVENTS} e WHERE e.visitor_id = v.id AND e.path = '{CONNECT_PATH}');
    DROP TABLE {LEGACY_EVENTS};
  END IF;
END $$;
"""

_BOT_UA = re.compile(r"bot|crawl|spider|slurp|preview|monitor|headless|lighthouse|curl|wget|python-|go-http|java/", re.I)

# Referrer host fragment -> source label shown in the admin.
_SOURCES = [
    ("google.", "Google"), ("bing.", "Bing"), ("duckduckgo.", "DuckDuckGo"), ("yahoo.", "Yahoo"),
    ("linkedin.", "LinkedIn"), ("lnkd.in", "LinkedIn"), ("instagram.", "Instagram"),
    ("facebook.", "Facebook"), ("fb.", "Facebook"), ("t.co", "X / Twitter"), ("twitter.", "X / Twitter"),
    ("x.com", "X / Twitter"), ("youtube.", "YouTube"), ("mail.", "Email"), ("outlook.", "Email"),
]


# ---------------------------------------------------------------------------
# Request parsing
# ---------------------------------------------------------------------------
def client_ip(req):
    forwarded = req.headers.get("X-Forwarded-For", "")
    return (forwarded.split(",")[0].strip() if forwarded else req.remote_addr) or ""


def is_bot(req):
    ua = req.headers.get("User-Agent", "")
    return not ua or bool(_BOT_UA.search(ua))


def _device(ua):
    if re.search(r"iPad|Tablet|Android(?!.*Mobile)", ua):
        return "Tablet"
    if re.search(r"Mobi|iPhone|Android", ua):
        return "Mobile"
    return "Desktop"


def _browser(ua):
    for pattern, name in (("Edg/", "Edge"), ("OPR/", "Opera"), ("SamsungBrowser", "Samsung Internet"),
                          ("Firefox/", "Firefox"), ("Chrome/", "Chrome"), ("Safari/", "Safari")):
        if pattern in ua:
            return name
    return "Other"


def _os(ua):
    for pattern, name in (("Windows", "Windows"), ("iPhone", "iOS"), ("iPad", "iPadOS"), ("Android", "Android"),
                          ("Mac OS X", "macOS"), ("CrOS", "ChromeOS"), ("Linux", "Linux")):
        if pattern in ua:
            return name
    return "Other"


def _source(req):
    utm = (req.args.get("utm_source") or "").strip()
    if utm:
        return utm[:40].title()
    referrer = req.referrer or ""
    host = (urlparse(referrer).hostname or "").lower()
    if not host or host == (req.host or "").split(":")[0].lower():
        return "Direct"
    return next((label for fragment, label in _SOURCES if fragment in host), "Referral")


# ---------------------------------------------------------------------------
# Background writer — requests enqueue, one daemon thread talks to Postgres
# ---------------------------------------------------------------------------
_queue = queue.Queue(maxsize=5000)
_worker = None
_worker_lock = threading.Lock()
_schema_ready = False


def _ensure_worker(app):
    global _worker
    with _worker_lock:
        if _worker is None or not _worker.is_alive():
            _worker = threading.Thread(target=_run, args=(app,), name="visitor-tracker", daemon=True)
            _worker.start()


def _enqueue(job):
    if not _dsn():
        return
    if SERVERLESS:
        # The process is frozen after the response, so a queued write would be
        # lost: do it now and accept the round trip.
        try:
            _write(*job)
        except Exception:
            logger.exception("Visitor tracking write failed for %s.", job[0])
        return
    _ensure_worker(current_app._get_current_object())
    try:
        _queue.put_nowait(job)
    except queue.Full:
        logger.warning("Visitor tracking queue full — dropping %s update.", job[0])


def _run(app):
    with app.app_context():
        while True:
            job = _queue.get()
            try:
                _write(*job)
            except Exception:
                logger.exception("Visitor tracking write failed for %s.", job[0])


def _ensure_schema(cur):
    global _schema_ready
    if not _schema_ready:
        cur.execute(SCHEMA)
        _schema_ready = True


def _write(kind, data):
    with _connect() as conn:
        with conn.cursor() as cur:
            _ensure_schema(cur)
            if kind == "pageview":
                _write_pageview(cur, data)
            elif kind == "module":
                _write_module(cur, data)
            elif kind == "identify":
                _write_identify(cur, data)
    if kind == "pageview" and data.get("_needs_geo"):
        _geolocate(data["visitor_key"], data["ip"])


def _local_day(ts):
    return ts.astimezone().date()


def _bump_day(cur, day, sessions=0, pageviews=0, bounces=0, seconds=0, hour=None, island=None,
              module=None, ms=0):
    """Add to one day's counters in a single upsert."""
    cur.execute(
        f"""
        INSERT INTO {DAILY} AS d (day, sessions, pageviews, bounces, session_seconds, hours, module_hits, module_ms, island_views)
        VALUES (%(day)s, %(sessions)s, %(pageviews)s, GREATEST(%(bounces)s, 0), %(seconds)s,
                %(hours)s::jsonb, %(hits)s::jsonb, %(ms)s::jsonb, %(islands)s::jsonb)
        ON CONFLICT (day) DO UPDATE SET
            sessions        = d.sessions + EXCLUDED.sessions,
            pageviews       = d.pageviews + EXCLUDED.pageviews,
            bounces         = GREATEST(d.bounces + %(bounces)s, 0),
            session_seconds = d.session_seconds + EXCLUDED.session_seconds,
            hours           = {PREFIX}_jsonb_add(d.hours, EXCLUDED.hours),
            module_hits     = {PREFIX}_jsonb_add(d.module_hits, EXCLUDED.module_hits),
            module_ms       = {PREFIX}_jsonb_add(d.module_ms, EXCLUDED.module_ms),
            island_views    = {PREFIX}_jsonb_add(d.island_views, EXCLUDED.island_views)
        """,
        {
            "day": day, "sessions": sessions, "pageviews": pageviews, "bounces": bounces, "seconds": seconds,
            "hours": json.dumps({str(hour): 1} if hour is not None else {}),
            "hits": json.dumps({module: 1} if module else {}),
            "ms": json.dumps({module: ms} if module else {}),
            "islands": json.dumps({island: 1} if island else {}),
        },
    )


def _write_pageview(cur, d):
    # One writer thread, so read-then-write is race free.
    cur.execute(
        f"SELECT id, sessions, last_seen, city, session_pages, session_started FROM {VISITORS} WHERE visitor_key = %s",
        (d["visitor_key"],),
    )
    row = cur.fetchone()
    at, day = d["at"], _local_day(d["at"])
    island = d["path"][len(ISLAND_PREFIX):].strip("/") if d["path"].startswith(ISLAND_PREFIX) else None
    connect = d["path"] == CONNECT_PATH

    if row is None:
        cur.execute(
            f"""
            INSERT INTO {VISITORS} (visitor_key, ip, source, referrer, landing_page, device, browser, os, user_agent,
                                    pages_viewed, first_seen, last_seen, last_page, last_title, saw_connect,
                                    session_started, session_pages)
            VALUES (%(visitor_key)s, %(ip)s, %(source)s, %(referrer)s, %(path)s, %(device)s, %(browser)s, %(os)s,
                    %(user_agent)s, 1, %(at)s, %(at)s, %(path)s, %(title)s, %(connect)s, %(at)s, 1)
            """,
            {**d, "connect": connect},
        )
        _bump_day(cur, day, sessions=1, pageviews=1, bounces=1, hour=at.astimezone().hour, island=island)
        d["_needs_geo"] = True
        return

    visitor_id, sessions, last_seen, city, session_pages, session_started = row
    d["_needs_geo"] = city in (None, "", "Local network")
    if at - last_seen > SESSION_GAP:
        # New session: counted as a bounce until a second page arrives.
        sessions, session_pages, session_started = sessions + 1, 1, at
        _bump_day(cur, day, sessions=1, pageviews=1, bounces=1, hour=at.astimezone().hour, island=island)
    else:
        session_pages += 1
        _bump_day(cur, day, pageviews=1, seconds=int((at - last_seen).total_seconds()), island=island)
        if session_pages == 2 and session_started:
            _bump_day(cur, _local_day(session_started), bounces=-1)  # not a bounce after all
    cur.execute(
        f"""
        UPDATE {VISITORS} SET sessions = %s, session_pages = %s, session_started = %s, pages_viewed = pages_viewed + 1,
               last_seen = %s, last_page = %s, last_title = %s, saw_connect = saw_connect OR %s,
               ip = %s, device = %s, browser = %s, os = %s, user_agent = %s
        WHERE id = %s
        """,
        (sessions, session_pages, session_started, at, d["path"], d["title"], connect,
         d["ip"], d["device"], d["browser"], d["os"], d["user_agent"], visitor_id),
    )


def _write_module(cur, d):
    cur.execute(
        f"UPDATE {VISITORS} SET module_ms = {PREFIX}_jsonb_add(module_ms, %s::jsonb) WHERE visitor_key = %s",
        (json.dumps({d["module"]: d["ms"]}), d["visitor_key"]),
    )
    if cur.rowcount:
        _bump_day(cur, _local_day(d["at"]), module=d["module"], ms=d["ms"])


def _write_identify(cur, d):
    cur.execute(
        f"""
        UPDATE {VISITORS} SET
            company = COALESCE(NULLIF(%(company)s, ''), company),
            name    = COALESCE(NULLIF(%(name)s, ''), name),
            email   = COALESCE(NULLIF(%(email)s, ''), email),
            converted_kind      = %(kind)s,
            converted_reference = %(reference)s,
            last_seen = %(at)s
        WHERE visitor_key = %(visitor_key)s
        """,
        d,
    )


def _geolocate(visitor_key, ip):
    """Fill city/region/country/network once per visitor.

    A private or loopback address (running locally, or a LAN visitor) has no
    location of its own, so it is looked up with a blank IP — the GeoIP service
    then answers for this server's public address, which is where that visitor is.
    """
    url = current_app.config.get("GEOIP_URL", "")
    if not url:
        return
    try:
        addr = ip_address(ip)
    except ValueError:
        return
    lookup_ip = "" if addr.is_private or addr.is_loopback else ip
    try:
        with urllib.request.urlopen(url.format(ip=lookup_ip), timeout=4) as resp:
            info = json.loads(resp.read().decode("utf-8"))
    except Exception:
        logger.warning("GeoIP lookup failed for a visitor.", exc_info=True)
        return
    if info.get("status") not in (None, "success"):
        return
    place = {
        "city": info.get("city") or "",
        "region": info.get("regionName") or info.get("region") or "",
        "country": info.get("country") or "",
        "network": info.get("org") or info.get("isp") or "",
    }
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE {VISITORS} SET city = %(city)s, region = %(region)s, country = %(country)s, "
                f"network = %(network)s WHERE visitor_key = %(key)s",
                {**place, "key": visitor_key},
            )


# ---------------------------------------------------------------------------
# Called from the app
# ---------------------------------------------------------------------------
def visitor_key(req):
    """The browser's tracking id, minting one (to be set as a cookie) when absent."""
    key = req.cookies.get(COOKIE, "")
    if re.fullmatch(r"[A-Za-z0-9_-]{16,64}", key):
        return key, False
    return secrets.token_urlsafe(18), True


def record_pageview(req, key, title):
    ua = req.headers.get("User-Agent", "")
    _enqueue(("pageview", {
        "visitor_key": key,
        "ip": client_ip(req),
        "source": _source(req),
        "referrer": (req.referrer or "")[:500],
        "path": req.path,
        "title": title,
        "device": _device(ua),
        "browser": _browser(ua),
        "os": _os(ua),
        "user_agent": ua[:500],
        "at": datetime.now(timezone.utc),
    }))


def record_module(req, module, ms, path):
    key = req.cookies.get(COOKIE, "")
    if not key or module not in MODULES or is_bot(req):
        return False
    _enqueue(("module", {
        "visitor_key": key,
        "module": module,
        "ms": max(0, min(int(ms), 30 * 60 * 1000)),
        "path": str(path or "")[:200],
        "at": datetime.now(timezone.utc),
    }))
    return True


def identify(kind, reference, fields):
    """Attach a /lets-connect submission to the browser that sent it."""
    key = request.cookies.get(COOKIE, "")
    if not key:
        return
    lookup = {str(label).lower(): value for label, value in fields}
    _enqueue(("identify", {
        "visitor_key": key,
        "kind": kind,
        "reference": reference,
        "company": str(lookup.get("company") or ""),
        "name": str(lookup.get("contact name") or lookup.get("name") or ""),
        "email": str(lookup.get("e-mail") or ""),
        "at": datetime.now(timezone.utc),
    }))


# ---------------------------------------------------------------------------
# Admin reads
# ---------------------------------------------------------------------------
def _fmt(ts):
    return ts.astimezone().strftime("%Y-%m-%d %H:%M") if ts else ""


def duration(seconds):
    seconds = int(round(seconds or 0))
    return f"{seconds // 60}m {seconds % 60:02d}s" if seconds >= 60 else f"{seconds}s"


def _status(row):
    if row.get("converted_reference"):
        return "Converted"
    return "Returning" if row["sessions"] > 1 else "New Lead"


def _shape(row):
    parts = [row.get("city"), row.get("region")]
    city = ", ".join(dict.fromkeys(p for p in parts if p)) or "Locating…"
    module_ms = {m: float(v) for m, v in (row.get("module_ms") or {}).items()}
    total_ms = sum(module_ms.values()) or 1
    return {
        **row,
        "label": f"Visitor #{row['id']}",
        "city": city,
        "country": row.get("country") or "—",
        "source": row.get("source") or "Direct",
        "device": row.get("device") or "Desktop",
        "module_ms": module_ms,
        "top_module": max(module_ms, key=lambda m: module_ms[m]) if module_ms else "—",
        # Time per module, largest first, for the visitor detail page.
        "attention": [
            {"module": m, "time": duration(ms / 1000), "pct": round(ms / total_ms * 100)}
            for m, ms in sorted(module_ms.items(), key=lambda kv: kv[1], reverse=True)
        ],
        "status": _status(row),
        "first_seen": _fmt(row.get("first_seen")),
        "last_seen": _fmt(row.get("last_seen")),
        "email": row.get("email") or "",
        "company": row.get("company") or "",
    }


# Query builders for store.query_batch — admin pages fetch everything in one round trip.
def visitors_query(limit=500):
    return f"SELECT * FROM {VISITORS} ORDER BY last_seen DESC LIMIT %s", (limit,)


def visitor_query(visitor_id):
    return f"SELECT * FROM {VISITORS} WHERE id = %s", (visitor_id,)


def daily_query(since_day):
    return f"SELECT * FROM {DAILY} WHERE day >= %s", (since_day,)


def count_query():
    return f"SELECT COUNT(*) AS n FROM {VISITORS}", ()


def shape_visitors(rows):
    return [_shape(r) for r in sorted(rows, key=lambda r: r["last_seen"], reverse=True)]


# Paginated Visitors list: status is derived, so it is computed in SQL too.
STATUS_SQL = ("CASE WHEN converted_reference IS NOT NULL THEN 'Converted' "
              "WHEN sessions > 1 THEN 'Returning' ELSE 'New Lead' END")
VISITOR_STATUSES = ("New Lead", "Returning", "Converted")
_SEARCH_COLUMNS = ("company", "name", "email", "city", "region", "country", "source", "network")


def _visitor_where(status=None, q=None):
    clauses, params = [], []
    if status in VISITOR_STATUSES:
        clauses.append(f"{STATUS_SQL} = %s")
        params.append(status)
    if q:
        clauses.append("(" + " OR ".join(f"{c} ILIKE %s" for c in _SEARCH_COLUMNS)
                       + " OR ('visitor #' || id::text) ILIKE %s)")
        params += [f"%{q}%"] * (len(_SEARCH_COLUMNS) + 1)
    return (" WHERE " + " AND ".join(clauses)) if clauses else "", params


def visitors_page_query(limit, offset, status=None, q=None):
    where, params = _visitor_where(status, q)
    return (f"SELECT * FROM {VISITORS}{where} ORDER BY last_seen DESC LIMIT %s OFFSET %s",
            tuple(params) + (limit, offset))


def visitors_count_query(status=None, q=None):
    where, params = _visitor_where(status, q)
    return f"SELECT COUNT(*) AS n FROM {VISITORS}{where}", tuple(params)


def visitor_status_counts_query(q=None):
    where, params = _visitor_where(None, q)
    return f"SELECT {STATUS_SQL} AS status, COUNT(*) AS n FROM {VISITORS}{where} GROUP BY 1", tuple(params)
