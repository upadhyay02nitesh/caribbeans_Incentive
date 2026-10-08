"""Crawler files: /robots.txt, /sitemap.xml and /favicon.ico.

Kept out of the `main` blueprint so the page-view tracker (routes/track.py,
main-only) never counts a crawler fetching them.
"""

from flask import Blueprint, Response, current_app, send_from_directory, url_for

from content import islands as islands_content

seo = Blueprint("seo", __name__)

# Public pages listed in the sitemap, in navigation order. Island pages are
# appended from content/islands.py so a new island is listed automatically.
SITEMAP_ENDPOINTS = [
    "main.index",
    "main.where_it_all_begins",
    "main.designed_around_you",
    "main.connected",
    "main.islands_index",
    "main.journey",
    "main.endless_creations",
    "main.envision",
    "main.connect",
]

# Never crawled: the dashboard, form POST targets, the chat API and the
# tracking beacons. CSS, JS and images stay crawlable so Google can render.
ROBOTS_DISALLOW = ["/admin", "/inquiry/", "/chat$", "/t$", "/t/"]


def _absolute(endpoint, **values):
    return current_app.config["SITE_URL"] + url_for(endpoint, **values)


@seo.route("/robots.txt")
def robots():
    lines = ["User-agent: *"]
    lines += [f"Disallow: {path}" for path in ROBOTS_DISALLOW]
    lines += ["Allow: /", "", f"Sitemap: {current_app.config['SITE_URL']}/sitemap.xml", ""]
    return Response("\n".join(lines), mimetype="text/plain",
                    headers={"Cache-Control": "public, max-age=3600"})


@seo.route("/sitemap.xml")
def sitemap():
    urls = [_absolute(e) for e in SITEMAP_ENDPOINTS]
    urls += [_absolute("main.island_detail", slug=i["slug"]) for i in islands_content.ISLANDS]
    body = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    body += [f"  <url><loc>{u}</loc></url>" for u in urls]
    body.append("</urlset>")
    return Response("\n".join(body) + "\n", mimetype="application/xml",
                    headers={"Cache-Control": "public, max-age=3600"})


@seo.route("/favicon.ico")
def favicon():
    # Browsers and Google's favicon fetcher ask for /favicon.ico regardless of
    # the <link rel="icon"> tags; serve the 48px brand mark instead of a 404.
    response = send_from_directory(current_app.static_folder, "img/brand/favicon-48.png",
                                   mimetype="image/png")
    response.headers["Cache-Control"] = "public, max-age=604800"
    return response
