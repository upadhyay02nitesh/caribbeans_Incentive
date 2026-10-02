"""Visitor tracking: a page-view hook for the public site and POST /t for
module dwell-time beacons from static/js/track.js. See services/visitors.py."""

from flask import Blueprint, request

from content.islands import ISLANDS
from content.site import NAV, NAV_CTA
from services import visitors

track = Blueprint("track", __name__)

_TITLES = {item["endpoint"]: item["title"] for item in NAV}
_TITLES.update({"main.index": "Home", NAV_CTA["endpoint"]: "Let's Connect"})
_ISLAND_NAMES = {i["slug"]: i["name"] for i in ISLANDS}


def _page_title():
    if request.endpoint == "main.island_detail":
        slug = (request.view_args or {}).get("slug", "")
        return f"Island · {_ISLAND_NAMES.get(slug, slug)}"
    return _TITLES.get(request.endpoint, request.path)


@track.after_app_request
def record_page_view(response):
    """Log successful public HTML page loads; admin, static, and bots are skipped."""
    if (request.blueprint != "main" or request.method != "GET" or response.status_code != 200
            or response.mimetype != "text/html" or visitors.is_bot(request)
            or request.headers.get("Purpose") == "prefetch"):
        return response
    key, minted = visitors.visitor_key(request)
    visitors.record_pageview(request, key, _page_title())
    if minted:
        response.set_cookie(visitors.COOKIE, key, max_age=visitors.COOKIE_MAX_AGE,
                            httponly=True, samesite="Lax", secure=request.is_secure)
    return response


@track.route("/t", methods=["POST"])
def beacon():
    data = request.get_json(force=True, silent=True) or {}
    for item in (data.get("modules") or [])[:10]:
        if isinstance(item, dict):
            try:
                visitors.record_module(request, item.get("module"), int(item.get("ms", 0)), data.get("path"))
            except (TypeError, ValueError):
                continue
    return "", 204
