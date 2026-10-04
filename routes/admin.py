import json
import math
from datetime import datetime
from urllib.parse import urlparse
from functools import wraps

import hmac
import secrets
from io import BytesIO

from flask import (Blueprint, abort, current_app, flash, g, redirect, render_template, request, send_file, session,
                   url_for)

from content import admin_mock
from services import analytics, sellsy, visitors as live_visitors
from services.storage import signed_url
from services.store import (AST, STATUSES, brief_value_query, counts_from, counts_query, find_inquiry,
                            inquiries_count_query, inquiries_page_query, inquiry_status_counts_query, inquiries_query,
                            last_read_error, query_batch, shape_briefs, shape_inquiries, update_status)
from forms import AdminLoginForm

admin = Blueprint("admin", __name__, url_prefix="/admin")


def _credentials_ok(username, password):
    """Check against ADMIN_USERNAME / ADMIN_PASSWORD from .env. Constant-time,
    and sign-in is refused outright when either value is missing."""
    expected_user = current_app.config.get("ADMIN_USERNAME", "")
    expected_pass = current_app.config.get("ADMIN_PASSWORD", "")
    if not expected_user or not expected_pass:
        return False
    user_ok = hmac.compare_digest((username or "").encode(), expected_user.encode())
    pass_ok = hmac.compare_digest((password or "").encode(), expected_pass.encode())
    return user_ok and pass_ok


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)

    return wrapped


@admin.app_template_filter("money")
def money(value):
    """Compact USD: 1300000 -> $1.3M, 175000 -> $175k."""
    value = value or 0
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M".replace(".0M", "M")
    if value >= 1_000:
        return f"${value / 1_000:.0f}k"
    return f"${value:,.0f}"


@admin.app_template_filter("eur")
def eur(value):
    """Compact EUR for Sellsy amounts: 175000 -> €175k, 1300000 -> €1.3M."""
    value = value or 0
    if value >= 1_000_000:
        return f"€{value / 1_000_000:.1f}M".replace(".0M", "M")
    if value >= 1_000:
        return f"€{value / 1_000:.0f}k"
    return f"€{value:,.0f}"


@admin.app_template_filter("initials")
def initials_filter(text):
    return admin_mock.initials(text)


def _csrf_token():
    """Per-session token for the admin's own POST forms (status changes)."""
    if "admin_csrf" not in session:
        session["admin_csrf"] = secrets.token_urlsafe(32)
    return session["admin_csrf"]


def _load(**queries):
    """One database round trip for the whole page: the page's own SELECTs plus
    the sidebar counts, which are stashed on `g` for inject_admin()."""
    data = query_batch({"nav_counts": counts_query(), "nav_visitors": live_visitors.count_query(), **queries})
    g.nav_counts = counts_from(data.pop("nav_counts"))
    visitors_total = data.pop("nav_visitors")
    g.nav_visitors = visitors_total[0]["n"] if visitors_total else 0
    return data


# ---------------------------------------------------------------------------
# Pagination — every admin list is paged and filtered on the server
# ---------------------------------------------------------------------------
PER_PAGE_CHOICES = (10, 25, 50, 100)
PER_PAGE_DEFAULT = 25


def _list_args():
    """(page, per_page, status, q) from the query string, sanitised."""
    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1
    try:
        per = int(request.args.get("per", PER_PAGE_DEFAULT))
    except ValueError:
        per = PER_PAGE_DEFAULT
    per = per if per in PER_PAGE_CHOICES else PER_PAGE_DEFAULT
    status = (request.args.get("status") or "").strip() or None
    q = (request.args.get("q") or "").strip()[:80]
    return page, per, status, q


def _paginate(total, page, per):
    pages = max(1, math.ceil(total / per))
    page = min(page, pages)
    start = (page - 1) * per
    # 1 … 4 5 [6] 7 8 … 20
    shown = sorted({1, pages, *range(max(1, page - 2), min(pages, page + 2) + 1)})
    window, last = [], 0
    for n in shown:
        if n - last > 1:
            window.append(None)
        window.append(n)
        last = n
    return {"page": page, "pages": pages, "per": per, "total": total, "start": start,
            "end": min(start + per, total), "prev": page - 1 if page > 1 else None,
            "next": page + 1 if page < pages else None, "window": window}


def _page_url(**changes):
    """Current list URL with some query args changed (None removes one)."""
    args = request.args.to_dict()
    for key, value in changes.items():
        if value is None:
            args.pop(key, None)
        else:
            args[key] = value
    if args.get("per") == str(PER_PAGE_DEFAULT):
        args.pop("per")
    return url_for(request.endpoint, **(request.view_args or {}), **args)


@admin.context_processor
def inject_admin():
    hour = datetime.now().hour
    if session.get("admin_logged_in") and "nav_counts" not in g:
        _load()
    # Sellsy warming used to run on every admin page via run_background(), which
    # is a real background thread on a long-lived server but runs INLINE on
    # Vercel (services/runtime.py) - so it was blocking every admin page on a
    # Sellsy API round trip whenever the snapshot went stale, even pages that
    # never show Sellsy data. The dashboard and Sellsy-tab routes already call
    # pipeline_snapshot() directly when they need it, so this was pure latency
    # tax on everything else.
    counts = g.get("nav_counts", {})
    return {
        "db_error": last_read_error() if session.get("admin_logged_in") else None,
        "admin_user": session.get("admin_username", "admin"),
        "greeting": "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening",
        "csrf_token": _csrf_token,
        "page_url": _page_url,
        "per_page_choices": PER_PAGE_CHOICES,
        "statuses": STATUSES,
        "nav_counts": {
            "visitors": g.get("nav_visitors", 0),
            "briefs_new": counts.get("brief", {}).get("new", 0),
            "rfps_total": counts.get("rfp", {}).get("total", 0),
            "rfps_new": counts.get("rfp", {}).get("new", 0),
            "callbacks_total": counts.get("callback", {}).get("total", 0),
            "callbacks_new": counts.get("callback", {}).get("new", 0),
        },
        "data_window": analytics.data_window(),
    }


@admin.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin.dashboard"))

    form = AdminLoginForm()
    error = None
    if form.validate_on_submit():
        if not current_app.config.get("ADMIN_USERNAME") or not current_app.config.get("ADMIN_PASSWORD"):
            error = "Admin sign-in is not configured — set ADMIN_USERNAME and ADMIN_PASSWORD in .env."
        elif _credentials_ok(form.username.data, form.password.data):
            session.clear()
            session["admin_logged_in"] = True
            session["admin_username"] = form.username.data
            return redirect(url_for("admin.dashboard"))
        else:
            error = "Incorrect username or password."

    return render_template("admin/login.html", form=form, error=error)


@admin.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)
    flash("You've been signed out.", "info")
    return redirect(url_for("admin.login"))


def _analytics():
    data = _load(briefs=inquiries_query("brief"), visitors=live_visitors.visitors_query(), **analytics.queries())
    return analytics.build(shape_briefs(data["briefs"]), live_visitors.shape_visitors(data["visitors"]), data)


@admin.route("/")
@login_required
def dashboard():
    # One round trip: the analytics reads plus per-status counts for every other tab.
    data = _load(briefs=inquiries_query("brief"), visitors=live_visitors.visitors_query(), **analytics.queries(),
                 st_brief=inquiry_status_counts_query("brief"), st_rfp=inquiry_status_counts_query("rfp"),
                 st_callback=inquiry_status_counts_query("callback"),
                 st_visitors=live_visitors.visitor_status_counts_query())
    live = analytics.build(shape_briefs(data["briefs"]), live_visitors.shape_visitors(data["visitors"]), data)
    summary = live["summary"]

    def by_status(rows, order):
        counts = {r["status"]: r["n"] for r in rows}
        return [(s, counts.get(s, 0)) for s in order]

    inboxes = {kind: by_status(data[f"st_{kind}"], STATUSES) for kind in ("brief", "rfp", "callback")}
    workspace = {
        "visitors": by_status(data["st_visitors"], live_visitors.VISITOR_STATUSES),
        "inboxes": inboxes,
        "totals": {kind: sum(n for _, n in rows) for kind, rows in inboxes.items()},
        "new": {kind: dict(rows).get("New", 0) for kind, rows in inboxes.items()},
        # every request across the three inboxes, by status
        "requests": [(s, sum(dict(rows).get(s, 0) for rows in inboxes.values())) for s in STATUSES],
    }
    sellsy_data, _age, sellsy_error = sellsy.pipeline_snapshot()  # in-memory, never waits on Sellsy

    # Ready-to-draw series for the workspace cards and donuts ({label, value, color}).
    def items(rows, colors):
        return [{"label": label, "value": n, "color": colors.get(label, "var(--a-muted)")} for label, n in rows]

    status_colors = {"New": "var(--a-lagoon-2)", "Contacted": "var(--a-gold)", "Qualified": "var(--a-sky)",
                     "Won": "var(--a-good)", "Lost": "#F29A86"}
    charts = {
        "visitors": items(workspace["visitors"], {"New Lead": "var(--a-lagoon-2)", "Returning": "var(--a-gold)",
                                                  "Converted": "var(--a-good)"}),
        "brief": items(inboxes["brief"], status_colors),
        "rfp": items(inboxes["rfp"], status_colors),
        "callback": items(inboxes["callback"], status_colors),
        "requests": items(workspace["requests"], status_colors),
        "channels": items([("Event briefs", workspace["totals"]["brief"]), ("RFP uploads", workspace["totals"]["rfp"]),
                           ("Callbacks", workspace["totals"]["callback"])],
                          {"Event briefs": "var(--s2)", "RFP uploads": "var(--s3)", "Callbacks": "var(--s1)"}),
    }
    if sellsy_data:
        labels = {"open": "Open", "late": "Late", "won": "Won", "lost": "Lost", "closed": "Closed"}
        opps = sellsy_data["opportunities"]
        charts["sellsy"] = items([(label, sum(1 for o in opps if o["status"] == key)) for key, label in labels.items()],
                                 {"Open": "var(--a-lagoon-2)", "Late": "var(--a-gold)", "Won": "var(--a-good)",
                                  "Lost": "#F29A86", "Closed": "var(--a-sky)"})
        charts["sellsy"] = [c for c in charts["sellsy"] if c["value"]]
    workspace["charts"] = charts
    chart_data = {
        "days": live["days"],
        "sessions": summary["sessions_daily"],
        "briefs": summary["briefs_daily"],
        "pipeline": summary["pipeline_daily"],
        "sources": live["traffic_sources"],
    }
    return render_template(
        "admin/dashboard.html",
        summary=summary,
        module_stats=live["module_stats"],
        island_views=live["island_views"],
        traffic_sources=live["traffic_sources"],
        activity=live["activity"],
        chart_json=json.dumps(chart_data),
        workspace=workspace,
        sellsy_data=sellsy_data, sellsy_error=sellsy_error,
        active_nav="dashboard",
    )


@admin.route("/export.xlsx")
@login_required
def export_report():
    """Branded Excel workbook of everything on the dashboard, one round trip."""
    from services import report  # openpyxl adds ~0.3 s to every cold start; only this route needs it

    data = _load(brief_rows=inquiries_query("brief", 5000), rfp_rows=inquiries_query("rfp", 5000),
                 callback_rows=inquiries_query("callback", 5000),
                 visitor_rows=live_visitors.visitors_query(5000), **analytics.queries())
    brief_list = shape_briefs(data["brief_rows"])
    visitor_list = live_visitors.shape_visitors(data["visitor_rows"])
    live = analytics.build(brief_list, visitor_list, data)
    sellsy_data, _age, _error = sellsy.pipeline_snapshot()
    xlsx = report.build_workbook({
        **live,
        "briefs": brief_list,
        "rfps": shape_inquiries(data["rfp_rows"]),
        "callbacks": shape_inquiries(data["callback_rows"]),
        "visitors": visitor_list,
        "sellsy": sellsy_data,
    })
    return send_file(BytesIO(xlsx), as_attachment=True,
                     download_name=f"caribbean-incentive-report-{datetime.now(AST):%Y-%m-%d}.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@admin.route("/visitors")
@login_required
def visitors():
    page, per, status, q = _list_args()
    data = _load(
        rows=live_visitors.visitors_page_query(per, (page - 1) * per, status, q),
        total=live_visitors.visitors_count_query(status, q),
        chips=live_visitors.visitor_status_counts_query(q),
        kpis=live_visitors.visitor_status_counts_query(),
    )
    p = _paginate(data["total"][0]["n"] if data["total"] else 0, page, per)
    if page > p["pages"]:
        return redirect(_page_url(page=p["pages"]))
    chip_counts = {r["status"]: r["n"] for r in data["chips"]}
    kpi_counts = {r["status"]: r["n"] for r in data["kpis"]}
    return render_template(
        "admin/visitors.html",
        visitors=live_visitors.shape_visitors(data["rows"]),
        p=p, status=status, q=q,
        chips=[(s, chip_counts.get(s, 0)) for s in live_visitors.VISITOR_STATUSES],
        chips_total=sum(chip_counts.values()),
        status_counts={s: kpi_counts.get(s, 0) for s in live_visitors.VISITOR_STATUSES},
        visitors_total=sum(kpi_counts.values()),
        active_nav="visitors",
    )


@admin.route("/visitors/<int:visitor_id>")
@login_required
def visitor_detail(visitor_id):
    data = _load(visitor=live_visitors.visitor_query(visitor_id), briefs=inquiries_query("brief"))
    if not data["visitor"]:
        abort(404)
    visitor = live_visitors.shape_visitors(data["visitor"])[0]
    brief = None
    if visitor.get("converted_kind") == "brief":
        brief = next((b for b in shape_briefs(data["briefs"]) if b["reference"] == visitor["converted_reference"]), None)
    return render_template(
        "admin/visitor_detail.html",
        visitor=visitor,
        brief=brief,
        brief_value=admin_mock.brief_value(brief) if brief else 0,
        active_nav="visitors",
    )


@admin.route("/analytics", endpoint="analytics")
@login_required
def analytics_page():
    live = _analytics()
    summary = live["summary"]
    chart_data = {
        "days": live["days"],
        "sessions": summary["sessions_daily"],
        "sources": live["traffic_sources"],
    }
    return render_template(
        "admin/analytics.html",
        summary=summary,
        traffic_sources=live["traffic_sources"],
        module_stats=live["module_stats"],
        island_page_views=live["island_views"],
        conversion_funnel=live["conversion_funnel"],
        chart_json=json.dumps(chart_data),
        active_nav="analytics",
    )


@admin.route("/sellsy")
@login_required
def sellsy_pipeline():
    data, age, error = sellsy.pipeline_snapshot(refresh=request.args.get("refresh") == "1")
    if request.args.get("refresh") == "1":
        return redirect(url_for("admin.sellsy_pipeline"))
    page, per, status, q = _list_args()
    rows, chips, chip_total, p = [], [], 0, _paginate(0, 1, per)
    if data:
        labels = {"open": "Open", "late": "Late", "won": "Won", "lost": "Lost", "closed": "Closed"}
        needle = q.lower()
        fields = ("number", "name", "company", "contact", "email", "step", "source")
        matched = [o for o in data["opportunities"]
                   if not needle or needle in " ".join(str(o[k]) for k in fields).lower()]
        chips = [(label, sum(1 for o in matched if o["status"] == key)) for key, label in labels.items()]
        chips = [c for c in chips if c[1]]
        chip_total = len(matched)
        if status:
            matched = [o for o in matched if labels.get(o["status"]) == status]
        p = _paginate(len(matched), page, per)
        if page > p["pages"]:
            return redirect(_page_url(page=p["pages"]))
        rows = matched[p["start"]:p["end"]]
    return render_template("admin/sellsy.html", data=data, age=age, error=error,
                           rows=rows, chips=chips, chips_total=chip_total, p=p, status=status, q=q,
                           stage_colors=["var(--a-lagoon-2)", "var(--a-gold)", "var(--a-sky)", "var(--s4)",
                                         "var(--s5)", "var(--a-good)"],
                           active_nav="sellsy")


@admin.route("/briefs")
@login_required
def briefs():
    page, per, status, q = _list_args()
    status = status if status in STATUSES else None
    data = _load(
        rows=inquiries_page_query("brief", per, (page - 1) * per, status, q),
        total=inquiries_count_query("brief", status, q),
        chips=inquiry_status_counts_query("brief", q),
        values=brief_value_query(),
    )
    # Stage totals cover every brief, whatever page or filter is showing.
    stages = []
    for stage in admin_mock.PIPELINE_STAGES:
        in_stage = [r for r in data["values"] if r["status"] == stage]
        stages.append({"stage": stage, "count": sum(r["n"] for r in in_stage),
                       "value": sum(r["n"] * admin_mock.BUDGET_MIDPOINTS.get(r["budget"], 0) for r in in_stage)})
    chip_counts = {r["status"]: r["n"] for r in data["chips"]}
    p = _paginate(data["total"][0]["n"] if data["total"] else 0, page, per)
    if page > p["pages"]:
        return redirect(_page_url(page=p["pages"]))
    return render_template(
        "admin/briefs.html",
        briefs=shape_briefs(data["rows"]),
        stages=stages,
        brief_value=admin_mock.brief_value,
        briefs_total=sum(st["count"] for st in stages),
        summary={"pipeline_value": sum(st["value"] for st in stages if st["stage"] != "Lost")},
        p=p, status=status, q=q,
        chips=[(s, chip_counts.get(s, 0)) for s in STATUSES if chip_counts.get(s)],
        chips_total=sum(chip_counts.values()),
        active_nav="briefs",
    )


# ---------------------------------------------------------------------------
# RFP uploads, callbacks and status changes — all read live from Postgres
# ---------------------------------------------------------------------------
def _inbox(kind):
    """One page of an inbox plus its totals and status chips."""
    page, per, status, q = _list_args()
    status = status if status in STATUSES else None
    data = _load(
        rows=inquiries_page_query(kind, per, (page - 1) * per, status, q),
        total=inquiries_count_query(kind, status, q),
        chips=inquiry_status_counts_query(kind, q),
        all=inquiries_count_query(kind),
    )
    chip_counts = {r["status"]: r["n"] for r in data["chips"]}
    p = _paginate(data["total"][0]["n"] if data["total"] else 0, page, per)
    if page > p["pages"]:
        return {"redirect": _page_url(page=p["pages"])}
    return {
        "rows": shape_inquiries(data["rows"]),
        "p": p,
        "status": status, "q": q,
        "chips": [(s, chip_counts.get(s, 0)) for s in STATUSES if chip_counts.get(s)],
        "chips_total": sum(chip_counts.values()),
        "grand_total": data["all"][0]["n"] if data["all"] else 0,
    }


@admin.route("/rfps")
@login_required
def rfps():
    box = _inbox("rfp")
    if "redirect" in box:
        return redirect(box["redirect"])
    n = box["grand_total"]
    return render_template(
        "admin/inbox.html",
        kind="rfp",
        title="RFP", title_em="uploads",
        eyebrow="Documents",
        lede=f"{n} RFP document{'s' if n != 1 else ''} received. Files are stored privately in Supabase Storage; download links are signed on demand.",
        **box,
        active_nav="rfps",
    )


@admin.route("/callbacks")
@login_required
def callbacks():
    box = _inbox("callback")
    if "redirect" in box:
        return redirect(box["redirect"])
    n = box["grand_total"]
    return render_template(
        "admin/inbox.html",
        kind="callback",
        title="Callback", title_em="requests",
        eyebrow="Follow-ups",
        lede=f"{n} callback request{'s' if n != 1 else ''}. Move each one along as the team makes contact.",
        **box,
        active_nav="callbacks",
    )


@admin.route("/rfps/<reference>/download")
@login_required
def rfp_download(reference):
    row = find_inquiry("rfp", reference)
    if not row or not row.get("file_path"):
        flash("That file isn't in storage — it may have been received before storage was connected, "
              "in which case it's attached to the notification email.", "warning")
        return redirect(url_for("admin.rfps"))
    # file_path is "<bucket>/<key>"; sign a short-lived link and hand it straight over.
    link = signed_url(row["file_path"].split("/", 1)[1], seconds=300)
    if not link:
        abort(503)
    return redirect(link)


@admin.route("/<kind>/<reference>/status", methods=["POST"])
@login_required
def set_status(kind, reference):
    if kind not in ("brief", "rfp", "callback"):
        abort(404)
    sent = request.form.get("csrf", "")
    if not hmac.compare_digest(sent, session.get("admin_csrf", "")):
        abort(400)
    status = request.form.get("status", "")
    if update_status(kind, reference, status):
        flash(f"{reference} moved to {status}.", "success")
    else:
        flash(f"Couldn't update {reference}.", "warning")
    back = url_for({"brief": "admin.briefs", "rfp": "admin.rfps", "callback": "admin.callbacks"}[kind])
    # Return to the same page / filter / search the change was made from (same-site admin URLs only).
    ref = urlparse(request.referrer or "")
    if ref.netloc == request.host and ref.path == back and ref.query:
        back += "?" + ref.query
    return redirect(back)
