"""Postgres storage for every /lets-connect submission.

Three tables, one per tab, all prefixed so they group together in the Supabase
table editor:

    caribbean_incentive_event_briefs    Submit an Event Brief
    caribbean_incentive_rfp_uploads     Upload an RFP
    caribbean_incentive_callbacks       Schedule a Call

Each keeps the tab's own fields as real columns (so they can be filtered and
sorted in the dashboard), plus `fields` as JSONB holding the raw submission —
nothing is lost if a form gains a field before the schema catches up — and
`emailed` / `whatsapped` recording whether each alert actually went out.

Configure with DATABASE_URL, or PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD, in
.env. Leave them blank and submissions go to instance/submissions.jsonl only —
the form never fails because the database is unreachable.

Note on pgvector: this data is structured and queried by column (kind, date,
company), so it needs no embeddings. pgvector would only earn its place if you
later want semantic search over the free-text brief — add an `embedding
vector(n)` column then, once an embedding model is in play.
"""

import json
import logging
import os
import re
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from flask import current_app

from services.runtime import SERVERLESS

# Saint-Martin's office time — Atlantic Standard Time, UTC-4 year-round, no DST.
# Every human-facing timestamp (admin lists, email/WhatsApp stamps) is shown in
# this zone regardless of where the server itself runs, so the team never has
# to convert UTC in their head. Storage stays UTC; only display converts.
AST = timezone(timedelta(hours=-4), name="AST")

logger = logging.getLogger(__name__)

PREFIX = "caribbean_incentive"

TABLES = {
    "brief": f"{PREFIX}_event_briefs",
    "rfp": f"{PREFIX}_rfp_uploads",
    "callback": f"{PREFIX}_callbacks",
}

# Columns each tab fills, mapped from the form labels used in routes/inquiry.py.
COLUMNS = {
    "brief": {
        "company": ("company",),
        "contact_name": ("contact name",),
        "email": ("e-mail",),
        "phone": ("phone",),
        "country": ("country",),
        "request_type": ("type of request",),
        "group_size": ("group size",),
        "preferred_dates": ("preferred dates",),
        "budget": ("average budget",),
        "message": ("about the event",),
    },
    "rfp": {
        "name": ("name",),
        "email": ("e-mail",),
        "company": ("company",),
        "file_name": ("attached file",),
        "file_type": ("file type",),
        "file_size": ("file size",),
        "file_url": ("file url",),
        "file_path": ("file path",),
    },
    "callback": {
        "name": ("name",),
        "email": ("e-mail",),
        "company": ("company",),
        "phone": ("phone",),
    },
}

_COMMON_TAIL = """
    status       TEXT NOT NULL DEFAULT 'New',
    fields       JSONB NOT NULL,
    emailed      BOOLEAN NOT NULL DEFAULT FALSE,
    whatsapped   BOOLEAN NOT NULL DEFAULT FALSE,
    source_ip    TEXT,
    user_agent   TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
"""

SCHEMA = f"""
CREATE TABLE IF NOT EXISTS {TABLES['brief']} (
    id              BIGSERIAL PRIMARY KEY,
    reference       TEXT UNIQUE NOT NULL,
    company         TEXT,
    contact_name    TEXT,
    email           TEXT,
    phone           TEXT,
    country         TEXT,
    request_type    TEXT,
    group_size      INTEGER,
    preferred_dates TEXT,
    budget          TEXT,
    message         TEXT,
{_COMMON_TAIL});

CREATE TABLE IF NOT EXISTS {TABLES['rfp']} (
    id         BIGSERIAL PRIMARY KEY,
    reference  TEXT UNIQUE NOT NULL,
    name       TEXT,
    email      TEXT,
    company    TEXT,
    file_name  TEXT,
    file_type  TEXT,
    file_size  INTEGER,
    file_url   TEXT,
    file_path  TEXT,
{_COMMON_TAIL});

CREATE TABLE IF NOT EXISTS {TABLES['callback']} (
    id        BIGSERIAL PRIMARY KEY,
    reference TEXT UNIQUE NOT NULL,
    name      TEXT,
    email     TEXT,
    company   TEXT,
    phone     TEXT,
{_COMMON_TAIL});

CREATE INDEX IF NOT EXISTS {TABLES['brief']}_created_idx ON {TABLES['brief']} (created_at DESC);
CREATE INDEX IF NOT EXISTS {TABLES['rfp']}_created_idx ON {TABLES['rfp']} (created_at DESC);
CREATE INDEX IF NOT EXISTS {TABLES['callback']}_created_idx ON {TABLES['callback']} (created_at DESC);
CREATE INDEX IF NOT EXISTS {TABLES['brief']}_email_idx ON {TABLES['brief']} (email);

-- migrations: columns added after a table was first created
ALTER TABLE {TABLES['brief']}    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'New';
ALTER TABLE {TABLES['rfp']}      ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'New';
ALTER TABLE {TABLES['callback']} ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'New';
ALTER TABLE {TABLES['rfp']}      ADD COLUMN IF NOT EXISTS file_type TEXT;
ALTER TABLE {TABLES['rfp']}      ADD COLUMN IF NOT EXISTS file_size INTEGER;
ALTER TABLE {TABLES['rfp']}      ADD COLUMN IF NOT EXISTS file_url TEXT;
ALTER TABLE {TABLES['rfp']}      ADD COLUMN IF NOT EXISTS file_path TEXT;
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_name = '{TABLES['rfp']}' AND column_name = 'contact_name') THEN
    ALTER TABLE {TABLES['rfp']} RENAME COLUMN contact_name TO name;
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_name = '{TABLES['rfp']}' AND column_name = 'filename') THEN
    ALTER TABLE {TABLES['rfp']} RENAME COLUMN filename TO file_name;
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_name = '{TABLES['callback']}' AND column_name = 'contact_name') THEN
    ALTER TABLE {TABLES['callback']} RENAME COLUMN contact_name TO name;
  END IF;
END $$;
"""

_schema_ready = False


def _dsn():
    return current_app.config.get("DATABASE_URL") or ""


_pool = None


def _pool_get():
    """Reuse a few open connections instead of a fresh DNS lookup + TLS
    handshake per query — the admin makes several queries per page."""
    global _pool
    if _pool is None:
        from psycopg2.pool import ThreadedConnectionPool

        dsn = _dsn()
        # Supabase requires TLS; add it unless the URL already says otherwise.
        if "sslmode=" not in dsn:
            dsn += ("&" if "?" in dsn else "?") + "sslmode=require"
        # Serverless spins up many instances: hold two slots each, not five.
        _pool = ThreadedConnectionPool(1, 2 if SERVERLESS else 5, dsn, connect_timeout=10,
                                       keepalives=1, keepalives_idle=30)
    return _pool


@contextmanager
def _connect():
    """Pooled connection: commits on success, rolls back on error, and drops a
    connection the server has closed so the next caller gets a fresh one."""
    import psycopg2  # imported lazily so the site runs without the driver

    pool = _pool_get()
    conn = pool.getconn()
    broken = False
    try:
        if conn.closed:
            pool.putconn(conn, close=True)
            conn = pool.getconn()
        yield conn
        conn.commit()
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        broken = True
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn, close=broken or bool(conn.closed))


def _archive(kind, reference, row, note):
    try:
        os.makedirs(current_app.instance_path, exist_ok=True)
        path = os.path.join(current_app.instance_path, "submissions.jsonl")
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "kind": kind,
                "reference": reference,
                "note": note,
                "row": row,
            }, default=str) + "\n")
    except Exception:
        logger.exception("Could not archive submission locally.")


def _row_for(kind, fields, reference, emailed, whatsapped, request):
    lookup = {str(label).lower(): value for label, value in fields}
    row = {"reference": reference}
    for column, labels in COLUMNS[kind].items():
        value = next((lookup[l] for l in labels if lookup.get(l) not in (None, "", [])), None)
        row[column] = value
    for column in ("group_size", "file_size"):
        if row.get(column) is not None:
            try:
                row[column] = int(row[column])
            except (TypeError, ValueError):
                row[column] = None
    row.update({
        "fields": {str(label): value for label, value in fields},
        "emailed": bool(emailed),
        "whatsapped": bool(whatsapped),
        "source_ip": (request.headers.get("X-Forwarded-For", request.remote_addr) if request else None),
        "user_agent": (request.headers.get("User-Agent") if request else None),
    })
    return row


def save_inquiry(kind, fields, reference, emailed=False, whatsapped=False, request=None):
    """Insert one submission into its tab's table. Returns True when stored."""
    if kind not in TABLES:
        logger.error("Unknown submission kind %r — not stored.", kind)
        return False

    row = _row_for(kind, fields, reference, emailed, whatsapped, request)

    if not _dsn():
        _archive(kind, reference, row, "DATABASE_URL not set; archived only")
        return False

    columns = list(row.keys())
    statement = (
        f"INSERT INTO {TABLES[kind]} ({', '.join(columns)}) "
        f"VALUES ({', '.join('%(' + c + ')s' for c in columns)}) "
        f"ON CONFLICT (reference) DO NOTHING"
    )
    params = {**row, "fields": json.dumps(row["fields"], default=str)}

    global _schema_ready
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                if not _schema_ready:
                    cur.execute(SCHEMA)
                    _schema_ready = True
                cur.execute(statement, params)
        logger.info("Stored %s %s in %s.", kind, reference, TABLES[kind])
        return True
    except Exception:
        logger.exception("Postgres insert failed for %s %s — archiving locally.", kind, reference)
        _archive(kind, reference, row, "Postgres insert failed; archived only")
        return False


STATUSES = ["New", "Contacted", "Qualified", "Won", "Lost"]


def update_status(kind, reference, status):
    """Move one submission to a pipeline stage. Returns True when a row changed."""
    if kind not in TABLES or status not in STATUSES or not _dsn():
        return False
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(f"UPDATE {TABLES[kind]} SET status = %s WHERE reference = %s", (status, reference))
                return cur.rowcount == 1
    except Exception:
        logger.exception("Could not update %s %s to %s", kind, reference, status)
        return False


def find_inquiry(kind, reference):
    """One submission by reference, or None."""
    if kind not in TABLES or not _dsn():
        return None
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT * FROM {TABLES[kind]} WHERE reference = %s", (reference,))
                row = cur.fetchone()
                return dict(zip([c[0] for c in cur.description], row)) if row else None
    except Exception:
        logger.exception("Could not load %s %s", kind, reference)
        return None


# ---------------------------------------------------------------------------
# Batched reads — the database is far away (~400 ms per round trip), so every
# admin page gathers all of its SELECTs into one statement, run outside a
# transaction: one round trip per page instead of three per query.
# ---------------------------------------------------------------------------
_TS_KEYS = {"created_at", "first_seen", "last_seen", "session_started"}
_TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d+))?([+-]\d{2})(?::?(\d{2}))?$")


def _parse_ts(value):
    """Postgres JSON timestamps -> aware datetimes (Python 3.10's fromisoformat is strict)."""
    m = _TS_RE.match(value) if isinstance(value, str) else None
    if not m:
        return value
    base, frac, tz_h, tz_m = m.groups()
    return datetime.fromisoformat(f"{base}.{(frac or '0')[:6].ljust(6, '0')}{tz_h}:{tz_m or '00'}")


def _ensure_all_schemas(cur):
    global _schema_ready
    if not _schema_ready:
        cur.execute(SCHEMA)
        _schema_ready = True
    from services import visitors  # lazy: visitors imports this module
    visitors._ensure_schema(cur)


_last_read_error = None


def last_read_error():
    """Why the most recent admin read came back empty, or None if it succeeded."""
    return _last_read_error


def query_batch(queries):
    """Run {name: (sql, params)} SELECTs in one round trip -> {name: [row dicts]}.

    Returns empty lists for every name when the database is unavailable.
    """
    global _last_read_error
    empty = {name: [] for name in queries}
    if not queries:
        return empty
    if not _dsn():
        _last_read_error = "DATABASE_URL is not set on this deployment."
        return empty
    parts, params = [], []
    for name, (sql, args) in queries.items():
        parts.append(f"'{name}', (SELECT COALESCE(json_agg(q), '[]'::json) FROM ({sql}) q)")
        params.extend(args)
    statement = "SELECT json_build_object(" + ", ".join(parts) + ")"
    try:
        with _connect() as conn:
            conn.autocommit = True  # plain reads: skip BEGIN/COMMIT round trips
            try:
                with conn.cursor() as cur:
                    _ensure_all_schemas(cur)
                    cur.execute(statement, params)
                    result = cur.fetchone()[0]
            finally:
                conn.autocommit = False
    except Exception as e:
        logger.exception("Batched admin read failed.")
        # psycopg2 messages name the host/user/port but never the password.
        _last_read_error = f"{type(e).__name__}: {str(e).strip()[:300]}"
        return empty
    _last_read_error = None
    for rows in result.values():
        for row in rows:
            for key in _TS_KEYS & row.keys():
                row[key] = _parse_ts(row[key])
    return result


def counts_query():
    return (" UNION ALL ".join(
        f"SELECT '{kind}' AS kind, COUNT(*) AS total, COUNT(*) FILTER (WHERE status = 'New') AS new FROM {table}"
        for kind, table in TABLES.items()), ())


def counts_from(rows):
    """{kind: {'total': n, 'new': n}} from counts_query() rows."""
    counts = {kind: {"total": 0, "new": 0} for kind in TABLES}
    for r in rows:
        counts[r["kind"]] = {"total": r["total"], "new": r["new"]}
    return counts


def inquiries_query(kind, limit=200):
    if kind not in TABLES:
        raise ValueError(kind)
    return f"SELECT * FROM {TABLES[kind]} ORDER BY created_at DESC LIMIT %s", (limit,)


def _newest_first(rows):
    return sorted(rows, key=lambda r: r.get("created_at") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)


def shape_briefs(rows):
    """Event-brief rows shaped for the admin dashboard (see routes/admin.py)."""
    briefs = []
    for r in _newest_first(rows):
        submitted = r.get("created_at")
        briefs.append({
            "id": r.get("id"),
            "reference": r.get("reference"),
            "company": r.get("company") or "—",
            "contact_name": r.get("contact_name") or "—",
            "email": r.get("email") or "",
            "country": r.get("country") or "—",
            "request_type": r.get("request_type") or "—",
            "group_size": r.get("group_size") or 0,
            "budget": r.get("budget") or "",
            "submitted_at": submitted.astimezone(AST).strftime("%Y-%m-%d %H:%M") + " AST" if submitted else "",
            "status": r.get("status") or "New",
            "phone": r.get("phone") or "",
            "preferred_dates": r.get("preferred_dates") or "",
            "message": r.get("message") or "",
            "emailed": bool(r.get("emailed")),
            "whatsapped": bool(r.get("whatsapped")),
        })
    return briefs


def shape_inquiries(rows):
    rows = _newest_first(rows)
    for r in rows:
        r["submitted_at"] = r["created_at"].astimezone(AST).strftime("%Y-%m-%d %H:%M") + " AST" if r.get("created_at") else ""
    return rows


# ---------------------------------------------------------------------------
# Paginated admin lists — rows, total and per-status counts, filtered by
# status and a search term on the server (ride the page's query_batch).
# ---------------------------------------------------------------------------
SEARCH_COLUMNS = {
    "brief": ("reference", "company", "contact_name", "email", "country", "request_type"),
    "rfp": ("reference", "company", "name", "email", "file_name"),
    "callback": ("reference", "company", "name", "email", "phone"),
}


def _inquiry_where(kind, status=None, q=None):
    clauses, params = [], []
    if status in STATUSES:
        clauses.append("status = %s")
        params.append(status)
    if q:
        cols = SEARCH_COLUMNS[kind]
        clauses.append("(" + " OR ".join(f"{c} ILIKE %s" for c in cols) + ")")
        params += [f"%{q}%"] * len(cols)
    return (" WHERE " + " AND ".join(clauses)) if clauses else "", params


def inquiries_page_query(kind, limit, offset, status=None, q=None):
    where, params = _inquiry_where(kind, status, q)
    return (f"SELECT * FROM {TABLES[kind]}{where} ORDER BY created_at DESC LIMIT %s OFFSET %s",
            tuple(params) + (limit, offset))


def inquiries_count_query(kind, status=None, q=None):
    where, params = _inquiry_where(kind, status, q)
    return f"SELECT COUNT(*) AS n FROM {TABLES[kind]}{where}", tuple(params)


def inquiry_status_counts_query(kind, q=None):
    where, params = _inquiry_where(kind, None, q)
    return f"SELECT status, COUNT(*) AS n FROM {TABLES[kind]}{where} GROUP BY status", tuple(params)


def brief_value_query():
    """Brief counts per stage and budget band — enough to value the whole pipeline."""
    return f"SELECT status, budget, COUNT(*) AS n FROM {TABLES['brief']} GROUP BY status, budget", ()
