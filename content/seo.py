"""Search and social metadata per public page: <title>, meta description, share image.

Keyed by endpoint so base.html can fill the <head> for every page from one place;
island pages are built from content/islands.py by island_meta(). No em dashes:
titles use " · " like the rest of the site. Keep titles under ~60 characters and
descriptions under ~160 so Google shows them uncut.
"""

from content.site import BRAND, CONTACT, DESCRIPTOR

# Production origin for canonical URLs, og:url, the sitemap and robots.txt.
# Overridable with SITE_URL in the environment (see config.py).
DEFAULT_SITE_URL = "https://www.caribbean-incentive.com"

PAGES = {
    "main.index": {
        "title": f"{BRAND} · Caribbean DMC & Incentive Travel",
        "description": (
            "Boutique Caribbean DMC for incentive travel, corporate meetings, conferences and "
            "group events in Saint Martin, St. Barth, Anguilla, the BVI, Dominica, Grenada and Barbados."
        ),
        "image": "island.saint-martin.hero",
    },
    "main.where_it_all_begins": {
        "title": f"Our Story · Boutique Caribbean DMC · {BRAND}",
        "description": (
            "Born in the Caribbean, Caribbean Incentive is a boutique destination management company "
            "combining local expertise and trusted partners to deliver seamless MICE programs."
        ),
        "image": "island.saint-martin.the-island",
        "crumb": "Where It All Begins",
    },
    "main.designed_around_you": {
        "title": f"Corporate Events & Incentive Services · {BRAND}",
        "description": (
            "End-to-end destination management in the Caribbean: incentive trips, executive retreats, "
            "conferences and gala events, with logistics, venues and on-site coordination."
        ),
        "image": "island.barbados.the-island",
        "crumb": "Designed Around You",
    },
    "main.connected": {
        "title": f"Caribbean Air Access & Direct Flights · {BRAND}",
        "description": (
            "How your group reaches the Caribbean: direct flights from the United States, Canada and "
            "Latin America, plus ferry and charter links between the islands we serve."
        ),
        "image": "island.british-virgin-islands.hero",
        "crumb": "Connected to the Caribbean",
    },
    "main.islands_index": {
        "title": f"Caribbean Destinations for Group Events · {BRAND}",
        "description": (
            "Seven Caribbean destinations for incentives, meetings and corporate events: Saint Martin, "
            "St. Barth, Anguilla, British Virgin Islands, Dominica, Grenada and Barbados."
        ),
        "image": "island.st-barth.hero",
        "crumb": "Explore Our Islands",
    },
    "main.journey": {
        "title": f"Caribbean Group Experiences & Team Building · {BRAND}",
        "description": (
            "Curated Caribbean experiences for corporate groups: island flavors, sailing, team "
            "building, local culture and quiet island moments, designed and run by our DMC team."
        ),
        "image": "experience.curated-experiences.1",
        "crumb": "Your Caribbean Journey",
    },
    "main.endless_creations": {
        "title": f"Why the Caribbean for Meetings & Incentives · {BRAND}",
        "description": (
            "Why choose the Caribbean for incentive travel and corporate gatherings: direct air "
            "access, easy island connections, rich cultures and unforgettable settings."
        ),
        "image": "island.grenada.experiences",
        "crumb": "Endless Creations",
    },
    "main.envision": {
        "title": f"Sample Itinerary & Planning Estimate · {BRAND}",
        "description": (
            "See how a five-day Caribbean incentive could unfold, then build an initial per-person "
            "planning estimate by island, group size, nights and program tier."
        ),
        "image": "itinerary.day4",
        "crumb": "Envision Your Experience",
    },
    "main.connect": {
        "title": f"Contact Us · Event Brief & RFP · {BRAND}",
        "description": (
            "Plan your Caribbean incentive, meeting or corporate event. Share an event brief, upload "
            "an RFP or request a callback from our team in Saint Martin."
        ),
        "image": "island.anguilla.hero",
        "crumb": "Let's Connect",
    },
}

# Endpoints that render a public page but must not be indexed: the /inquiry/*
# POSTs re-render connect.html in place, so they borrow its copy and canonical.
# Ownership tokens rendered as <meta name=... content=...> in every page's <head>
# (server-rendered, so crawlers see them without JavaScript). Not secrets.
SITE_VERIFICATION = {
    # Meta Business portfolio "Caribbean incentive" -> Brand safety -> Domains.
    "facebook-domain-verification": "9ys9f6dt9qfwqmzl2pwvja4czhhwmr",
}

ALIASES = {
    "inquiry.brief": "main.connect",
    "inquiry.rfp": "main.connect",
    "inquiry.callback": "main.connect",
}

FALLBACK = {
    "title": f"{BRAND} · Caribbean DMC & Incentive Travel",
    "description": PAGES["main.index"]["description"],
    "image": "hero_poster",
}


def island_meta(island):
    """Title/description for an island page, from the island's own client copy."""
    name = island["name"]
    place = f"the {name}" if name.startswith("British") else name
    return {
        "title": f"{name} DMC & Incentive Travel · {BRAND}",
        "description": (
            f"Plan incentive trips, corporate retreats, meetings and group events in {place} "
            f"with {BRAND}, a boutique Caribbean DMC with local expertise."
        ),
        "image": f"island.{island['slug']}.hero",
        "crumb": name,
    }


# ---------------------------------------------------------------------------
# Structured data (JSON-LD). Only facts already published on the site: no
# ratings, reviews, opening hours or social profiles (SOCIALS are still "#").
# ---------------------------------------------------------------------------
def organization(site_url, logo_url, island_names):
    office = CONTACT["offices"][0]
    return {
        "@type": "TravelAgency",
        "@id": f"{site_url}/#organization",
        "name": BRAND,
        "description": f"{DESCRIPTOR}: incentive travel, corporate meetings, conferences and group events.",
        "url": f"{site_url}/",
        "logo": logo_url,
        "image": logo_url,
        "email": CONTACT["email"],
        "telephone": CONTACT["phone"].replace(" ", ""),
        "address": {
            "@type": "PostalAddress",
            "streetAddress": office["lines"][0].split(",")[0].strip(),
            "addressLocality": "Marigot",
            "postalCode": "97150",
            "addressRegion": "Saint-Martin",
            "addressCountry": "MF",
        },
        "areaServed": [{"@type": "Place", "name": n} for n in island_names],
        "knowsAbout": ["Destination management", "Incentive travel", "Corporate events",
                       "Meetings and conferences", "MICE"],
    }


def website(site_url):
    return {
        "@type": "WebSite",
        "@id": f"{site_url}/#website",
        "url": f"{site_url}/",
        "name": BRAND,
        "publisher": {"@id": f"{site_url}/#organization"},
        "inLanguage": "en",
    }
