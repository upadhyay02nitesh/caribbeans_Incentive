"""Live figures for the admin Dashboard and Analytics pages.

Computed over a rolling 14-day window from the compact counters kept by
services/visitors.py — the per-day totals table plus the visitor rows — and
the event-brief table (services/store.py), in the same shapes the templates
were built around. queries() is merged into the page's store.query_batch call,
so the whole page is one database round trip.
"""

from collections import Counter, defaultdict
from datetime import date, timedelta

from content.admin_mock import brief_value, engagement_level, pipeline_by_stage
from content.islands import ISLANDS
from services import visitors as v

WINDOW_DAYS = 14
MODULE_ORDER = ["Regional Map", "Estimator", "Island Detail", "Itinerary", "Hero", "Getting There"]


def window_days():
    today = date.today()
    return [today - timedelta(days=i) for i in range(WINDOW_DAYS - 1, -1, -1)]


def data_window():
    days = window_days()
    first, last = days[0], days[-1]
    left = f"{first.day} {first:%b}" if first.month != last.month else f"{first.day}"
    return f"{left} – {last.day} {last:%b %Y}"


def queries():
    """SELECTs for store.query_batch — the page's other reads ride the same round trip."""
    return {"a_daily": v.daily_query(window_days()[0])}


def _pct_change(current, previous):
    return round((current - previous) / previous * 100, 1) if previous else None


def _sum_json(rows, field):
    total = defaultdict(float)
    for r in rows:
        for key, value in (r.get(field) or {}).items():
            total[key] += float(value)
    return total


def _activity(visitors, limit=7):
    """Most recent visitors and what they last did — from the visitor rows."""
    labels = {"brief": "Submitted Event Brief", "rfp": "Uploaded an RFP", "callback": "Requested a callback"}
    feed = []
    for x in visitors[:limit]:
        event = labels.get(x.get("converted_kind")) or f"Viewed {x.get('last_title') or x.get('last_page') or 'the site'}"
        feed.append({
            "time": x["last_seen"],
            "event": event,
            "detail": f"{x['city']} · via {x['source']}",
            "visitor_id": x["id"],
            "visitor": x["label"],
            "company": x["company"] or x.get("name") or "",
        })
    return feed


def build(briefs, all_visitors, raw):
    """Everything the Dashboard and Analytics templates render, from the rows
    returned by queries() plus the shaped briefs and visitors."""
    days = window_days()
    day_keys = [d.isoformat() for d in days]
    daily = {str(r["day"])[:10]: r for r in raw["a_daily"]}
    rows = list(daily.values())

    # --- sessions, bounce, duration, peak hour -----------------------------
    sessions_daily = [int(daily[d]["sessions"]) if d in daily else 0 for d in day_keys]
    total_sessions = sum(sessions_daily)
    this_week, last_week = sum(sessions_daily[-7:]), sum(sessions_daily[-14:-7])
    bounces = sum(int(r["bounces"]) for r in rows)
    seconds = sum(int(r["session_seconds"]) for r in rows)
    hours = _sum_json(rows, "hours")
    peak_hour = ""
    if hours:
        h = int(max(hours, key=lambda k: hours[k]))
        peak_hour = f"{(h % 12) or 12}–{((h + 1) % 12) or 12} {'AM' if h < 12 else 'PM'}"

    # --- modules -------------------------------------------------------------
    hits, module_ms = _sum_json(rows, "module_hits"), _sum_json(rows, "module_ms")
    module_stats = [
        {
            "module": m,
            "views": int(hits[m]),
            "engagement_rate": min(100, round(hits[m] / total_sessions * 100)) if total_sessions else 0,
            "avg_time_sec": round(module_ms[m] / hits[m] / 1000) if hits[m] else 0,
        }
        for m in MODULE_ORDER
    ]
    top_module = max(module_stats, key=lambda m: (m["engagement_rate"], m["views"]))

    # --- islands -------------------------------------------------------------
    island_counts = _sum_json(rows, "island_views")
    island_views = sorted(
        ({"island": i["name"], "slug": i["slug"], "views": int(island_counts[i["slug"]])} for i in ISLANDS),
        key=lambda i: i["views"], reverse=True,
    )

    # --- visitors: sources, devices, funnel, conversion ----------------------
    since = day_keys[0]
    recent = [x for x in all_visitors if x["last_seen"][:10] >= since]
    sources = Counter(x["source"] for x in recent).most_common()
    traffic_sources = [{"source": s, "visitors": n} for s, n in sources[:4]]
    if len(sources) > 4:
        traffic_sources.append({"source": "Other", "visitors": sum(n for _, n in sources[4:])})
    devices = Counter(x["device"] for x in recent)
    device_total = sum(devices.values())
    device_split = {d: round(devices[d] / device_total * 100) if device_total else 0
                    for d in ("Desktop", "Mobile", "Tablet")}

    conversion_funnel = [
        {"stage": "Visitors", "count": len(recent)},
        {"stage": "Engaged with a module", "count": sum(1 for x in recent if x["module_ms"])},
        {"stage": "Used the Estimator", "count": sum(1 for x in recent if "Estimator" in x["module_ms"])},
        {"stage": "Opened Connect", "count": sum(1 for x in recent if x.get("saw_connect"))},
        {"stage": "Submitted a Brief", "count": sum(1 for x in recent if x.get("converted_kind") == "brief")},
    ]

    total_visitors = len(all_visitors)
    converted = sum(1 for x in all_visitors if x["status"] == "Converted")
    engaged = sum(1 for x in all_visitors if engagement_level(x)[1] >= 2)

    # --- briefs + pipeline ---------------------------------------------------
    briefs_daily = [sum(1 for b in briefs if b["submitted_at"][:10] == d) for d in day_keys]
    before = sum(brief_value(b) for b in briefs if b["submitted_at"][:10] < day_keys[0] and b["status"] != "Lost")
    pipeline_daily, running = [], before
    for d in day_keys:
        running += sum(brief_value(b) for b in briefs if b["submitted_at"][:10] == d and b["status"] != "Lost")
        pipeline_daily.append(running)
    stages = pipeline_by_stage(briefs)

    summary = {
        "total_visitors": total_visitors,
        "total_briefs": len(briefs),
        "top_module": top_module,
        "conversion_rate": round(converted / total_visitors * 100) if total_visitors else 0,
        "converted": converted,
        "recent_briefs": sorted(briefs, key=lambda b: b["submitted_at"], reverse=True)[:5],
        "recent_visitors": all_visitors[:6],
        "engagement_avg": round(engaged / total_visitors * 100) if total_visitors else 0,
        "quick_stats": {
            "avg_session_duration": v.duration(seconds / total_sessions) if total_sessions else "—",
            "bounce_rate": min(100, round(bounces / total_sessions * 100)) if total_sessions else 0,
            "device_split": device_split,
            "top_referrer": sources[0][0] if sources else "—",
            "peak_traffic_hour": peak_hour or "—",
        },
        "sessions_14d": total_sessions,
        "sessions_week": this_week,
        "sessions_delta": _pct_change(this_week, last_week),
        "sessions_daily": sessions_daily,
        "briefs_daily": briefs_daily,
        "briefs_week": sum(briefs_daily[-7:]),
        "pipeline_value": sum(s["value"] for s in stages if s["stage"] != "Lost"),
        "pipeline_daily": pipeline_daily,
        "won_value": next(s["value"] for s in stages if s["stage"] == "Won"),
        "stages": stages,
        "awaiting_reply": next(s["count"] for s in stages if s["stage"] == "New"),
        "site_conversion": round(conversion_funnel[-1]["count"] / len(recent) * 100, 1) if recent else 0,
    }
    return {
        "summary": summary,
        "days": day_keys,
        "module_stats": module_stats,
        "island_views": island_views,
        "traffic_sources": traffic_sources,
        "conversion_funnel": conversion_funnel,
        "activity": _activity(all_visitors),
    }
