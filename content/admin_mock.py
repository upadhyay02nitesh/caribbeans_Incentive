"""Admin helpers and business constants (no demo data).

Every figure the admin shows is live — visitors from services/visitors.py,
dashboard/analytics from services/analytics.py, inquiries from
services/store.py. This module only holds the pipeline valuation rules and
small helpers those share.
"""


def engagement_level(visitor):
    """Return (label, star_count) estimating a visitor's interest level from
    how many pages they viewed and how many sessions they returned for."""
    score = visitor["pages_viewed"] + visitor["sessions"] * 2
    if score >= 15:
        return "High", 3
    if score >= 8:
        return "Medium", 2
    return "Low", 1


# Planning midpoint (USD) for each budget band on the brief form — used to
# value the pipeline. "Not sure yet" carries no value until qualified.
BUDGET_MIDPOINTS = {
    "Under $100k": 75_000,
    "$100k–250k": 175_000,
    "$250k–500k": 375_000,
    "$500k+": 500_000,
    "Not sure yet": 0,
}

PIPELINE_STAGES = ["New", "Contacted", "Qualified", "Won", "Lost"]


def brief_value(brief):
    return BUDGET_MIDPOINTS.get(brief["budget"], 0)


def initials(text):
    words = [w for w in str(text).replace("&", " ").split() if w[:1].isalpha()]
    return "".join(w[0] for w in words[:2]).upper() or "—"


def pipeline_by_stage(briefs):
    stages = []
    for stage in PIPELINE_STAGES:
        items = [b for b in briefs if b["status"] == stage]
        stages.append({
            "stage": stage,
            "count": len(items),
            "value": sum(brief_value(b) for b in items),
        })
    return stages
