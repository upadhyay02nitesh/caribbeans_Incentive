"""Sellsy CRM integration for all three /lets-connect forms (Sellsy API v2).

Every event brief, RFP upload and callback request becomes, in Sellsy:
  * a company (found by name, or created as a prospect),
  * a contact (found by e-mail, or created) linked to that company,
  * an opportunity in the "Tunnel de vente CARAIBES INCENTIVE" pipeline, at the
    first step ("1er contact / prise de brief"), source "Formulaire demande de
    devis site internet", with every form field in the note. Briefs are valued
    at the budget band's planning midpoint; RFPs get the document attached.

Auth is OAuth2 client-credentials (SELLSY_CLIENT_ID / SELLSY_CLIENT_SECRET);
the token is cached until shortly before it expires. The work runs on a
background thread so the visitor never waits on Sellsy, and any failure — or
missing credentials — falls back to appending the brief to
instance/submissions.jsonl. The form never shows an error because of Sellsy.

IDs below are from this account's setup (GET /v2/opportunities/pipelines,
/pipelines/{id}/steps, /opportunities/sources) and can be overridden in .env.
"""

import json
import logging
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html import escape

from flask import current_app

from services.runtime import run_background

from content.admin_mock import BUDGET_MIDPOINTS

logger = logging.getLogger(__name__)

TOKEN_URL = "https://login.sellsy.com/oauth2/access-tokens"
API = "https://api.sellsy.com/v2"

_token = {"value": None, "expires": 0.0}
_token_lock = threading.Lock()


class SellsyError(Exception):
    pass


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------
def _access_token(client_id, client_secret):
    with _token_lock:
        if _token["value"] and time.time() < _token["expires"]:
            return _token["value"]
        body = urllib.parse.urlencode({"grant_type": "client_credentials", "client_id": client_id,
                                       "client_secret": client_secret}).encode()
        req = urllib.request.Request(TOKEN_URL, data=body, headers={
            "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        _token["value"] = data["access_token"]
        _token["expires"] = time.time() + int(data.get("expires_in", 3600)) - 120
        return _token["value"]


def _call(token, method, path, body=None):
    req = urllib.request.Request(
        API + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json",
                 "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raise SellsyError(f"{method} {path} -> {e.code}: {e.read().decode(errors='replace')[:400]}") from None


# ---------------------------------------------------------------------------
# CRM records
# ---------------------------------------------------------------------------
def _find_or_create_company(token, name, email, phone, country, owner_id=None):
    found = _call(token, "POST", "/companies/search?limit=25", {"filters": {"name": name}}).get("data", [])
    match = next((c for c in found if (c.get("name") or "").strip().lower() == name.strip().lower()), None)
    if match:
        return match["id"]
    created = _call(token, "POST", "/companies", {
        "name": name, "type": "prospect", "email": email or None, "phone_number": phone or None,
        "note": escape(f"Created from the website brief form. Country: {country or '—'}"),
        **({"owner_id": owner_id} if owner_id else {}),
    })
    return created["id"]


def _split_name(full):
    parts = (full or "").strip().split()
    if len(parts) < 2:
        return "", parts[0] if parts else "Website contact"
    return " ".join(parts[:-1]), parts[-1]


def _find_or_create_contact(token, full_name, email, phone, company_id, owner_id=None):
    if email:
        found = _call(token, "POST", "/contacts/search?limit=5", {"filters": {"email": email}}).get("data", [])
        if found:
            return found[0]["id"]
    first, last = _split_name(full_name)
    contact = _call(token, "POST", "/contacts", {
        "first_name": first or None, "last_name": last, "email": email or None, "phone_number": phone or None,
        **({"owner_id": owner_id} if owner_id else {}),
    })
    try:
        _call(token, "POST", f"/companies/{company_id}/contacts/{contact['id']}", {})
    except SellsyError as e:  # linking is a nicety — never fail the opportunity over it
        logger.warning("Sellsy: could not link contact %s to company %s: %s", contact["id"], company_id, e)
    return contact["id"]


KIND_TITLES = {"brief": "Event brief", "rfp": "RFP document", "callback": "Callback request"}


def _note(kind, reference, fields):
    rows = [("Website form", KIND_TITLES[kind]), ("Website reference", reference)] + list(fields)
    return "".join(f"<p><strong>{escape(str(label))}:</strong> {escape(str(value))}</p>"
                   for label, value in rows if value not in (None, ""))


def _attach(token, opportunity_id, attachment):
    """Upload the RFP document to the opportunity (multipart/form-data)."""
    filename, mimetype, data = attachment
    boundary = "----ci" + os.urandom(12).hex()
    safe_name = filename.replace('"', "")
    head = (f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{safe_name}"\r\n'
            f"Content-Type: {mimetype}\r\n\r\n").encode()
    body = head + data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(f"{API}/opportunities/{opportunity_id}/files", data=body, method="POST", headers={
        "Authorization": f"Bearer {token}", "Accept": "application/json",
        "Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        raise SellsyError(f"file upload -> {e.code}: {e.read().decode(errors='replace')[:300]}") from None


def _push(config, kind, payload, attachment=None):
    """Company -> contact -> opportunity (-> attached file). Returns the opportunity id."""
    token = _access_token(config["SELLSY_CLIENT_ID"], config["SELLSY_CLIENT_SECRET"])
    person = payload.get("contact_name") or payload.get("name")
    company_name = (payload.get("company") or "").strip() or person or "Website enquiry"
    # Records are owned by SELLSY_OWNER_ID so they show up for that user (Sellsy users may only see their own).
    owner_id = int(config["SELLSY_OWNER_ID"]) if config.get("SELLSY_OWNER_ID") else None
    company_id = _find_or_create_company(token, company_name, payload.get("email"), payload.get("phone"),
                                         payload.get("country"), owner_id)
    contact_id = _find_or_create_contact(token, person, payload.get("email"), payload.get("phone"), company_id,
                                         owner_id)

    if kind == "brief":
        title = f"{company_name} — {payload.get('request_type') or 'Event brief'}"
        if payload.get("group_size"):
            title += f" ({payload['group_size']} pax)"
    else:
        title = f"{company_name} — {KIND_TITLES[kind]}"
    body = {
        "name": title,
        "pipeline": int(config["SELLSY_PIPELINE_ID"]),
        "step": int(config["SELLSY_STEP_ID"]),
        "source": int(config["SELLSY_SOURCE_ID"]),
        "related": [{"type": "company", "id": company_id}],
        "contact_ids": [contact_id],
        "note": _note(kind, payload.get("reference"), payload.get("fields", [])),
    }
    if owner_id:
        body.update({"owner_id": owner_id, "assigned_staff_ids": [owner_id]})
    if kind == "brief":
        body["amount"] = str(BUDGET_MIDPOINTS.get(payload.get("budget"), 0))
    opportunity_id = _call(token, "POST", "/opportunities", body).get("id")

    if attachment and opportunity_id:
        try:
            _attach(token, opportunity_id, attachment)
        except SellsyError as e:  # the note still names the file — don't fail the lead over the upload
            logger.warning("Sellsy: could not attach %s to opportunity %s: %s", attachment[0], opportunity_id, e)
    return opportunity_id


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------
def send_to_sellsy(kind, reference, fields, attachment=None, **extra):
    """Send one /lets-connect submission to Sellsy in the background.

    `fields` is the form's (label, value) list — the same one stored in
    Postgres — so the Sellsy note always matches the admin. `extra` carries the
    few values Sellsy needs as real fields (company, name, email, phone, country,
    budget, request_type, group_size). `attachment` is (filename, mimetype, bytes).
    Always returns True: failures are logged and archived locally.
    """
    payload = {"reference": reference, "fields": [(str(k), v) for k, v in fields], **extra}
    config = current_app.config
    if not config.get("SELLSY_CLIENT_ID") or not config.get("SELLSY_CLIENT_SECRET"):
        logger.info("Sellsy credentials not configured — logging %s %s locally.", kind, reference)
        _append_jsonl(current_app.instance_path, kind, payload, "Sellsy not configured")
        return True

    settings = {k: config.get(k) for k in ("SELLSY_CLIENT_ID", "SELLSY_CLIENT_SECRET", "SELLSY_PIPELINE_ID",
                                          "SELLSY_STEP_ID", "SELLSY_SOURCE_ID", "SELLSY_OWNER_ID")}
    instance_path = current_app.instance_path

    def work():
        try:
            opportunity_id = _push(settings, kind, payload, attachment)
            logger.info("Sellsy opportunity %s created for %s %s", opportunity_id, kind, reference)
        except Exception as e:
            logger.exception("Sellsy push failed for %s %s — archived locally.", kind, reference)
            _append_jsonl(instance_path, kind, payload, f"Sellsy push failed: {e}")

    run_background(work, name="sellsy-push")
    return True


def _append_jsonl(instance_path, kind, payload, note):
    try:
        os.makedirs(instance_path, exist_ok=True)
        with open(os.path.join(instance_path, "submissions.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(), "kind": f"sellsy-{kind}",
                                "note": note, "payload": payload}, default=str) + "\n")
    except Exception:
        logger.exception("Could not archive Sellsy payload locally.")


# ---------------------------------------------------------------------------
# Admin "Sellsy" tab — a cached snapshot of the pipeline, so the page never
# waits on Sellsy: it renders the last snapshot instantly and refreshes it in
# the background once it is older than SNAPSHOT_TTL seconds.
# ---------------------------------------------------------------------------
SNAPSHOT_TTL = 60
_snapshot = {"data": None, "fetched": 0.0, "error": None, "refreshing": False}
_snapshot_lock = threading.Lock()


def _fetch_pipeline(config):
    token = _access_token(config["SELLSY_CLIENT_ID"], config["SELLSY_CLIENT_SECRET"])
    pipeline_id = int(config["SELLSY_PIPELINE_ID"])
    website_source = int(config["SELLSY_SOURCE_ID"])
    steps = _call(token, "GET", f"/opportunities/pipelines/{pipeline_id}/steps").get("data", [])

    rows, offset = [], None
    for _ in range(20):  # 100 per page; 20 pages is far beyond this pipeline's size
        query = "?limit=100&order=created&direction=desc&embed[]=company&embed[]=contacts&embed[]=individual"
        if offset:
            query += "&offset=" + urllib.parse.quote(offset)
        page = _call(token, "POST", "/opportunities/search" + query, {"filters": {"pipeline": [pipeline_id]}})
        rows += page.get("data", [])
        pag = page.get("pagination", {})
        offset = pag.get("offset")
        if not offset or pag.get("count", 0) < 100 or len(rows) >= pag.get("total", 0):
            break

    opportunities = []
    for o in rows:
        embed = o.get("_embed") or {}
        company = embed.get("company") or {}
        individual = embed.get("individual") or {}  # private clients are individuals, not companies
        contact = (embed.get("contacts") or [{}])[0] or individual
        amount = float((o.get("amount") or {}).get("value") or 0)
        opportunities.append({
            "id": o["id"],
            "number": o.get("number") or "",
            "name": o.get("name") or "",
            "company": company.get("name") or " ".join(
                p for p in (individual.get("first_name"), individual.get("last_name")) if p),
            "is_individual": not company and bool(individual),
            "contact": " ".join(p for p in (contact.get("first_name"), contact.get("last_name")) if p),
            "email": contact.get("email") or "",
            "step": (o.get("step") or {}).get("name") or "—",
            "step_id": (o.get("step") or {}).get("id"),
            "status": o.get("status") or "open",
            "amount": amount,
            "currency": (o.get("amount") or {}).get("currency") or "EUR",
            "source": ((o.get("source") or {}).get("name") or "—").strip(),
            "is_website": (o.get("source") or {}).get("id") == website_source,
            "created": (o.get("created") or "")[:10],
        })

    live = [o for o in opportunities if o["status"] in ("open", "late")]
    stages = []
    for s in steps:
        in_step = [o for o in live if o["step_id"] == s["id"]]
        stages.append({"name": s["name"], "probability": s.get("probability"),
                       "count": len(in_step), "value": sum(o["amount"] for o in in_step)})
    won = [o for o in opportunities if o["status"] == "won"]
    return {
        "pipeline": (rows[0].get("pipeline") or {}).get("name") if rows else "",
        "opportunities": opportunities,
        "stages": stages,
        "open_count": len(live),
        "open_value": sum(o["amount"] for o in live),
        "weighted_value": sum(o["amount"] * (next((s.get("probability") or 0 for s in steps if s["id"] == o["step_id"]), 0)) / 100
                              for o in live),
        "website_count": sum(1 for o in opportunities if o["is_website"]),
        "won_count": len(won),
        "won_value": sum(o["amount"] for o in won),
        "total": len(opportunities),
    }


def _refresh_snapshot(config):
    try:
        data = _fetch_pipeline(config)
        with _snapshot_lock:
            _snapshot.update(data=data, fetched=time.time(), error=None)
    except Exception as e:
        logger.exception("Sellsy snapshot refresh failed.")
        with _snapshot_lock:
            _snapshot["error"] = str(e)[:200]
    finally:
        with _snapshot_lock:
            _snapshot["refreshing"] = False


def pipeline_snapshot(refresh=False):
    """(data or None, age_seconds or None, error). Never blocks: a stale or
    missing snapshot triggers a background refresh."""
    config = current_app.config
    if not config.get("SELLSY_CLIENT_ID") or not config.get("SELLSY_CLIENT_SECRET"):
        return None, None, "Sellsy is not configured."
    with _snapshot_lock:
        stale = refresh or time.time() - _snapshot["fetched"] > SNAPSHOT_TTL
        if stale and not _snapshot["refreshing"]:
            _snapshot["refreshing"] = True
            settings = {k: config.get(k) for k in ("SELLSY_CLIENT_ID", "SELLSY_CLIENT_SECRET",
                                                  "SELLSY_PIPELINE_ID", "SELLSY_SOURCE_ID")}
            run_background(_refresh_snapshot, settings, name="sellsy-snapshot")
        age = time.time() - _snapshot["fetched"] if _snapshot["data"] else None
        return _snapshot["data"], age, _snapshot["error"]
