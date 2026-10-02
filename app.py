import os
import re
from datetime import datetime

from flask import Flask, render_template, request, url_for

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

    app.register_blueprint(main)
    app.register_blueprint(inquiry)
    app.register_blueprint(admin)
    app.register_blueprint(chat)
    app.register_blueprint(track)

    from content import site as site_content
    from content import islands as islands_content
    from content.media import img as media_img
    from content import media as media_content
    from content.admin_mock import engagement_level

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
        }

    @app.after_request
    def no_store_admin(response):
        # /admin is session-gated (login state, which user) - a shared browser
        # or edge cache serving a stale copy under this path would leak one
        # session's view to another, so it must never be cached.
        if request.blueprint == "admin":
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        return response

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"], host="127.0.0.1", port=5000)
