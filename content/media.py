"""Single registry for every image/video URL used across the site.

Swapping in real client photography later is a one-file change: replace the
paths below (and drop matching files under static/) — no template changes
needed. See scripts/fetch_placeholders.py for how demo imagery is sourced.
"""

from flask import url_for

ISLAND_SLUGS = [
    "saint-martin",
    "st-barth",
    "anguilla",
    "british-virgin-islands",
    "dominica",
    "grenada",
    "barbados",
]

EXPERIENCE_SLUGS = [
    "curated-experiences",
    "caribbean-legacy",
    "island-flavors",
    "across-sand-and-sea",
    "crafted-in-the-caribbean",
    "unique-team-building-experiences",
    "quiet-island-moments",
    "the-art-of-execution",
    "sustainability-and-authenticity",
]

MEDIA = {
    # Real client brand mark (static/img/brand/, derived from "Logo - CI.webp"):
    # logo-full is the icon + wordmark lockup (footer); logo-mark is the icon
    # alone (header, next to the styled text wordmark; also the favicon source).
    "brand.logo": "img/brand/logo-full.png",
    "brand.mark": "img/brand/logo-mark.png",
    "hero_video": "video/hero.mp4",
    "hero_video_webm": "video/hero.webm",
    "hero_poster": "img/hero-poster.jpg",
    "hero_scene_1": "img/hero/scene-1.jpg",
    "hero_scene_2": "img/hero/scene-2.jpg",
    "hero_scene_3": "img/hero/scene-3.jpg",
    "hero_scene_4": "img/hero/scene-4.jpg",
    "fallback": "img/fallback.jpg",
    # Real client photo (not stock) — the contact portrait on /lets-connect.
    "team.portrait": "img/team/portrait.png",
    # Chat widget avatar (header + every assistant reply), cropped from the client's cut-out portrait.
    "team.chat": "img/team/chat-avatar.png",
}

# Island hero + card + 3 panel images each
for slug in ISLAND_SLUGS:
    MEDIA[f"island.{slug}.hero"] = f"img/islands/{slug}/hero.jpg"
    MEDIA[f"island.{slug}.card"] = f"img/islands/{slug}/card.jpg"
    MEDIA[f"island.{slug}.the-island"] = f"img/islands/{slug}/the-island.jpg"
    MEDIA[f"island.{slug}.gastronomy"] = f"img/islands/{slug}/gastronomy.jpg"
    MEDIA[f"island.{slug}.experiences"] = f"img/islands/{slug}/experiences.jpg"

# Experience gallery — 6 images per category
for slug in EXPERIENCE_SLUGS:
    for i in range(1, 7):
        MEDIA[f"experience.{slug}.{i}"] = f"img/experiences/{slug}/{i}.jpg"

# Itinerary day images
for i in range(1, 6):
    MEDIA[f"itinerary.day{i}"] = f"img/itinerary/day{i}.jpg"


def img(key, fallback_key="fallback"):
    """Return a static URL for a media key, falling back gracefully if missing."""
    path = MEDIA.get(key) or MEDIA.get(fallback_key)
    return url_for("static", filename=path)
