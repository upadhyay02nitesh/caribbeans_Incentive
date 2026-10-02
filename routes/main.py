import json

from flask import Blueprint, current_app, render_template, url_for

from content import experiences as experiences_content
from content import islands as islands_content
from content import itinerary as itinerary_content
from content import pricing as pricing_content
from content import services as services_content
from content import site as site_content
from content.media import img as media_img
from forms import EventBriefForm, RfpForm, CallbackForm

main = Blueprint("main", __name__)


def build_map_data():
    data = {}
    for isle in islands_content.ISLANDS:
        chips = islands_content.CONNECTIONS.get(isle["slug"], [])
        data[isle["slug"]] = {
            "name": isle["name"],
            "intro": isle["headline"],
            "chips": [{"mode": m, "time": t, "note": n} for m, t, n in chips],
            "url": url_for("main.island_detail", slug=isle["slug"]),
            "image": media_img(f"island.{isle['slug']}.card"),
            "access": isle["access"],
        }
    return json.dumps(data)


def build_airlift_data():
    """Direct flights as JSON for the route diagram (static/js/map.js)."""
    data = {}
    for island in islands_content.DIRECT_FLIGHTS:
        data[island["slug"]] = {
            "name": island["name"],
            "code": island.get("code", ""),
            "routes": [{"city": city, "time": time, "seasonal": bool(seasonal)}
                       for city, time, seasonal in island["routes"]],
        }
    return json.dumps(data)


def build_facts():
    counts = {
        "destinations": len(islands_content.ISLANDS),
        "islands": len(islands_content.GETTING_THERE),
        "origins": len(islands_content.ORIGINS),
        "services": len(services_content.JOURNEY),
    }
    return [
        {"value": counts[key], "label": label, "note": note}
        for key, (label, note) in site_content.FACT_LABELS.items()
    ]


@main.route("/")
def index():
    return render_template(
        "index.html",
        hero=site_content.HERO,
        intro=site_content.HOME_INTRO,
        where_it_all_begins=site_content.WHERE_IT_ALL_BEGINS,
        explore=site_content.EXPLORE_OUR_CARIBBEAN,
        designed_around_you=site_content.DESIGNED_AROUND_YOU,
        endless_creations=site_content.ENDLESS_CREATIONS,
        islands=islands_content.ISLANDS,
        experiences=experiences_content.EXPERIENCES,
        experiences_intro=experiences_content.EXPERIENCES_INTRO,
        experiences_home=experiences_content.EXPERIENCES_HOME,
        journey_section=services_content.JOURNEY_SECTION,
        journey=services_content.JOURNEY,
        map_data_json=build_map_data(),
        map_center=islands_content.MAP_CENTER,
        map_extra_islands=islands_content.MAP_EXTRA_ISLANDS,
        map_gateways=islands_content.MAP_GATEWAYS,
        testimonials=site_content.TESTIMONIALS,
        facts=build_facts(),
    )


@main.route("/where-it-all-begins")
def where_it_all_begins():
    return render_template("where_it_all_begins.html", content=site_content.WHERE_IT_ALL_BEGINS)


@main.route("/designed-around-you")
def designed_around_you():
    return render_template(
        "designed_around_you.html",
        content=site_content.DESIGNED_AROUND_YOU,
        service_categories=services_content.SERVICE_CATEGORIES,
        journey_section=services_content.JOURNEY_SECTION,
        journey=services_content.JOURNEY,
    )


@main.route("/connected-to-the-caribbean")
def connected():
    return render_template(
        "connected.html",
        islands=islands_content.ISLANDS,
        connections=islands_content.CONNECTIONS,
        getting_there=islands_content.GETTING_THERE,
        facts=build_facts(),
        origins=islands_content.ORIGINS,
        direct_flights=islands_content.DIRECT_FLIGHTS,
        airlift_label=islands_content.AIRLIFT_LABEL,
        airlift_seasonal=islands_content.AIRLIFT_SEASONAL_NOTE,
        airlift_json=build_airlift_data(),
        disclaimer=islands_content.GETTING_THERE_DISCLAIMER,
        map_data_json=build_map_data(),
        map_center=islands_content.MAP_CENTER,
        map_extra_islands=islands_content.MAP_EXTRA_ISLANDS,
        map_gateways=islands_content.MAP_GATEWAYS,
    )


@main.route("/explore-our-islands")
def islands_index():
    return render_template(
        "islands_index.html",
        islands=islands_content.ISLANDS,
        explore=site_content.EXPLORE_OUR_CARIBBEAN,
        connections=islands_content.CONNECTIONS,
        closer=site_content.EXPLORE_OUR_CARIBBEAN["closer"],
    )


@main.route("/explore-our-islands/<slug>")
def island_detail(slug):
    island = islands_content.get_island(slug)
    if island is None:
        from flask import abort
        abort(404)
    return render_template(
        "island_detail.html",
        island=island,
        next_island=islands_content.next_island(slug),
        island_index=islands_content.ISLANDS.index(island) + 1,
        island_count=len(islands_content.ISLANDS),
        connections=islands_content.CONNECTIONS.get(slug, []),
    )


@main.route("/your-caribbean-journey")
def journey():
    return render_template(
        "journey.html",
        intro=experiences_content.EXPERIENCES_INTRO,
        closer=experiences_content.EXPERIENCES_CLOSER,
        experiences=experiences_content.EXPERIENCES,
    )


@main.route("/endless-creations")
def endless_creations():
    return render_template(
        "endless_creations.html",
        content=site_content.ENDLESS_CREATIONS,
        experiences=experiences_content.EXPERIENCES,
        islands=islands_content.ISLANDS,
    )


@main.route("/envision-your-experience")
def envision():
    itinerary_json = json.dumps(
        [
            {"day": d, "title": t, "desc": desc, "image": media_img(f"itinerary.day{i}")}
            for i, (d, t, desc) in enumerate(itinerary_content.ITINERARY, start=1)
        ]
    )
    return render_template(
        "envision.html",
        content=site_content.ENVISION,
        itinerary_kicker=itinerary_content.ITINERARY_KICKER,
        itinerary_note=itinerary_content.ITINERARY_NOTE,
        itinerary=itinerary_content.ITINERARY,
        itinerary_json=itinerary_json,
        islands=islands_content.ISLANDS,
        tiers=pricing_content.TIERS,
        addons=pricing_content.ADDONS,
        estimator_copy=pricing_content.ESTIMATOR_COPY,
        estimator_disclaimer=pricing_content.ESTIMATOR_DISCLAIMER,
        estimator_islands=pricing_content.ISLAND_RATES,
        island_rate_json=json.dumps(pricing_content.ISLAND_RATE),
        service_fee=pricing_content.SERVICE_FEE,
    )


@main.route("/lets-connect")
def connect():
    return render_template(
        "connect.html",
        content=site_content.CONNECT,
        contact=site_content.CONTACT,
        brief_form=EventBriefForm(),
        rfp_form=RfpForm(),
        callback_form=CallbackForm(),
        teams_booking_url=current_app.config.get("TEAMS_BOOKING_URL"),
        whatsapp_number=current_app.config.get("WHATSAPP_NUMBER"),
        active_tab="brief",
    )
