import json
import logging
import os
import re
from datetime import datetime

from flask import Flask, redirect, render_template, request, url_for
from werkzeug.exceptions import HTTPException

from markupsafe import Markup, escape

from config import Config
from services.runtime import SERVERLESS, TMP_INSTANCE


def md_bold(text):
    """Render the **bold** markers used in content/ copy as <strong>, escaping the rest."""
    parts = str(escape(text)).split("**")
    return Markup("".join(f"<strong>{p}</strong>" if i % 2 else p for i, p in enumerate(parts)))


def lead(text, sentences=1):
    """First `sentences` sentences of a copy string — keeps pages compact without editing content/."""
    parts = re.split(r"(?<=[.!?])\s+", str(text).strip())
    return " ".join(parts[:sentences])


def create_app(config_class=Config):
    # Serverless hosts have a read-only filesystem apart from /tmp.
    app = Flask(__name__, instance_relative_config=True,
                instance_path=TMP_INSTANCE if SERVERLESS else None)
    app.config.from_object(config_class)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(os.path.join(app.instance_path, "rfps"), exist_ok=True)

    from routes.main import main
    from routes.inquiry import inquiry
    from routes.admin import admin
    from routes.chat import chat
    from routes.track import track
    from routes.seo import seo

    app.register_blueprint(main)
    app.register_blueprint(inquiry)
    app.register_blueprint(admin)
    app.register_blueprint(chat)
    app.register_blueprint(track)
    app.register_blueprint(seo)

    if SERVERLESS and app.config["SECRET_KEY"] == "dev-key-not-secure":
        logging.getLogger(__name__).warning(
            "FLASK_SECRET_KEY is not set: admin sessions are signed with the public default key.")

    from content import site as site_content
    from content import islands as islands_content
    from content.media import img as media_img
    from content import media as media_content
    from content.admin_mock import engagement_level
    from content import seo as seo_content

    app.jinja_env.globals["img"] = media_img
    app.jinja_env.filters["md_bold"] = md_bold
    app.jinja_env.filters["lead"] = lead
    app.jinja_env.globals["engagement_level"] = engagement_level

    def _hero_video_files():
        """Hero scenes play as video when clips exist in static/video/.

        Drop hero-1.mp4, hero-2.mp4, hero-3.mp4 (or a single hero.mp4) in there and
        they replace the photo crossfade — no template change needed.
        """
        folder = os.path.join(app.static_folder, "video")
        if not os.path.isdir(folder):
            return []
        clips = sorted(
            f for f in os.listdir(folder)
            if f.lower().startswith("hero") and f.lower().endswith((".mp4", ".webm"))
        )
        mimes = {".mp4": "video/mp4", ".webm": "video/webm"}
        return [
            {"src": url_for("static", filename=f"video/{f}"), "type": mimes[os.path.splitext(f)[1].lower()]}
            for f in clips
        ]

    def _page_meta():
        """Title, description, canonical, share image and JSON-LD for this request."""
        site_url = app.config["SITE_URL"]
        endpoint = seo_content.ALIASES.get(request.endpoint, request.endpoint)
        meta = seo_content.PAGES.get(endpoint)
        if endpoint == "main.island_detail":
            island = islands_content.get_island((request.view_args or {}).get("slug", ""))
            meta = seo_content.island_meta(island) if island else None
        public = meta is not None
        meta = dict(meta or seo_content.FALLBACK)

        # Canonical is the clean production URL of the page itself (never the
        # query string); /inquiry/* re-renders point at /lets-connect.
        canonical = None
        if public:
            path = url_for(endpoint, **(request.view_args or {})) if endpoint != request.endpoint else request.path
            canonical = site_url + path
        image = media_img(meta["image"])
        meta.update(canonical=canonical,
                    image=image if image.startswith("http") else site_url + image)

        graph = []
        if endpoint == "main.index":
            logo = site_url + url_for("static", filename="img/brand/logo-full.png")
            graph += [seo_content.organization(site_url, logo, [i["name"] for i in islands_content.ISLANDS]),
                      seo_content.website(site_url)]
        if canonical and endpoint != "main.index":
            crumbs = [("Home", site_url + "/")]
            if endpoint == "main.island_detail":
                crumbs.append(("Explore Our Islands", site_url + url_for("main.islands_index")))
            crumbs.append((meta.get("crumb", meta["title"]), canonical))
            graph.append({"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": n, "name": name, "item": url}
                for n, (name, url) in enumerate(crumbs, start=1)]})
        if graph:
            # "</" escaped so copy can never close the <script> block early.
            meta["jsonld"] = Markup(json.dumps({"@context": "https://schema.org", "@graph": graph},
                                               ensure_ascii=False).replace("</", "<\\/"))
        return meta

    @app.context_processor
    def inject_globals():
        return {
            "nav": site_content.NAV,
            "nav_cta": site_content.NAV_CTA,
            "nav_islands": islands_content.ISLANDS,
            "brand": site_content.BRAND,
            "brand_descriptor": site_content.DESCRIPTOR,
            "tagline": site_content.TAGLINE,
            "domain": site_content.DOMAIN,
            "marquee": site_content.MARQUEE,
            "cta_bands": site_content.CTA_BANDS,
            "footer": site_content.FOOTER,
            "contact": site_content.CONTACT,
            "socials": site_content.SOCIALS,
            "hero_video_files": _hero_video_files(),
            # Per-domain visitor tracking; empty off the live domains.
            "tracking_script": site_content.tracking_script_for(
                os.environ.get("TRACKING_HOST") or request.host),
            "current_year": datetime.now().year,
            "page_meta": _page_meta(),
            "site_verification": seo_content.SITE_VERIFICATION,
        }

    @app.after_request
    def no_store_admin(response):
        # /admin is session-gated (login state, which user) - a shared browser
        # or edge cache serving a stale copy under this path would leak one
        # session's view to another, so it must never be cached.
        # Checked by path, not request.blueprint: Flask's automatic trailing-
        # slash redirect (/admin -> /admin/) fires before the blueprint is
        # resolved, so blueprint is None on that response and it slipped past
        # the blueprint check with a cacheable default.
        if request.path.startswith("/admin"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        return response

    @app.after_request
    def security_and_robots_headers(response):
        headers = response.headers
        headers.setdefault("X-Content-Type-Options", "nosniff")
        headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        # Geolocation stays allowed for this origin: track.js asks for GPS once.
        headers.setdefault("Permissions-Policy", "camera=(), microphone=(), payment=(), geolocation=(self)")
        # Keep everything that is not a public page out of search results,
        # and keep Vercel preview/deployment hosts from competing with www.
        internal = request.blueprint in ("admin", "inquiry", "chat", "track")
        if internal or request.host.split(":")[0].endswith(".vercel.app"):
            headers["X-Robots-Tag"] = "noindex, nofollow"
        return response

    @app.errorhandler(404)
    def not_found(e):
        # /explore-our-islands/ and friends: one permanent hop to the real URL
        # instead of a 404 (Flask routes here are defined without the slash).
        path = request.path
        if request.method == "GET" and len(path) > 1 and path.endswith("/"):
            try:
                app.url_map.bind("").match(path.rstrip("/"), method="GET")
            except HTTPException:
                pass
            else:
                query = request.query_string.decode()
                return redirect(path.rstrip("/") + (f"?{query}" if query else ""), code=301)
        return render_template("404.html"), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"], host="127.0.0.1", port=5000)
