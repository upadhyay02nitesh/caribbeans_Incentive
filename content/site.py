"""Global site copy: nav, hero, footer, contact, CTAs. All copy is client-final — verbatim."""

BRAND = "Caribbean Incentive"
TAGLINE = "Your People, Our Home, Caribbean Connection"
DOMAIN = "caribbean-incentive.com"
RFP_EMAIL = "karishma.singh@caribbean-incentive.com"

CONTACT = {
    "email": RFP_EMAIL,
    "phone": "+590 690 66 22 88",
    "hours": [
        ("North America & Caribbean", "6:00 AM – 6:00 PM AST"),
        ("Europe (France)", "12:00 PM – 8:00 PM"),
    ],
    # Portrait card under the contact list on /lets-connect.
    "partner": {
        "image": "team.portrait",
        "eyebrow": "Your Caribbean partner",
        "line": "Personal attention from the first conversation to the final farewell.",
    },
    "offices": [
        # "map" is the Google Maps search used by the office map on /lets-connect.
        {"name": "St. Martin / St. Maarten", "lines": ["Rue Général de Gaulle, Marigot", "97150 SAINT-MARTIN"],
         "map": "Rue General de Gaulle, Marigot, 97150 Saint-Martin"},
    ],
}
CONTACT["address"] = ", ".join(CONTACT["offices"][0]["lines"])


# ---------------------------------------------------------------------------
# Website-visitor tracking (ColdIQ / websitevisitors.ai) — one script per
# domain, injected in <head> by the base template. Matched on the request host
# so each brand's traffic reaches its own account; anything else (localhost,
# preview deployments) gets no script, keeping test traffic out of the client's
# analytics. Set TRACKING_HOST in .env to force one while testing.
# ---------------------------------------------------------------------------
TRACKING_SCRIPTS = {
    "caraibes-incentive.com": "https://coldiq.websitevisitors.ai/s/lBJOm_lR6PHkkr5ErR-p_A.js",
    "caribbean-incentive.com": "https://coldiq.websitevisitors.ai/s/uzPJU1-AeqhCB8A3Xqz7-A.js",
}


def tracking_script_for(host):
    """The tracking script for a request host, or "" when it is not a live domain."""
    name = (host or "").split(":")[0].strip().lower()
    if name.startswith("www."):
        name = name[4:]
    return TRACKING_SCRIPTS.get(name, "")

# "short" is the condensed header label used below ~1700px; "title" is the
# display-case label used in the full-screen menu; "image" is a
# content/media.py key previewed when the item is hovered.
NAV = [
    {"label": "WHERE IT ALL BEGINS", "title": "Where It All Begins", "endpoint": "main.where_it_all_begins", "short": "OUR STORY", "image": "island.saint-martin.the-island"},
    {"label": "DESIGNED AROUND YOU", "title": "Designed Around You", "endpoint": "main.designed_around_you", "short": "WHAT WE DO", "image": "island.barbados.the-island"},
    {"label": "CONNECTED TO THE CARIBBEAN", "title": "Connected to the Caribbean", "endpoint": "main.connected", "short": "CONNECTED", "image": "island.british-virgin-islands.hero"},
    {"label": "EXPLORE OUR ISLANDS", "title": "Explore Our Islands", "endpoint": "main.islands_index", "short": "ISLANDS", "has_dropdown": True, "image": "island.st-barth.hero"},
    {"label": "YOUR CARIBBEAN JOURNEY", "title": "Your Caribbean Journey", "endpoint": "main.journey", "short": "EXPERIENCES", "image": "experience.across-sand-and-sea.1"},
    {"label": "ENDLESS CREATIONS", "title": "Endless Creations", "endpoint": "main.endless_creations", "short": "WHY CARIBBEAN", "image": "island.grenada.experiences"},
    {"label": "ENVISION YOUR EXPERIENCE", "title": "Envision Your Experience", "endpoint": "main.envision", "short": "ENVISION", "image": "itinerary.day4"},
]

NAV_CTA = {"label": "LET'S CONNECT", "endpoint": "main.connect"}

DESCRIPTOR = "Boutique Caribbean DMC"

# Service lines scrolled in the marquee bands (drawn from SERVICE_CATEGORIES).
MARQUEE = [
    "Incentive Travel Programs",
    "Corporate Meetings",
    "Executive Retreats",
    "International Conferences",
    "Gala Dinners & Private Events",
    "Multi-island Programs",
]

# Labels for the homepage figures row — the numbers are counted from content
# data in routes/main.py so they can never drift out of sync.
FACT_LABELS = {
    "destinations": ("Destinations", "Full island programs"),
    "islands": ("Islands served", "Across the Eastern Caribbean"),
    "origins": ("Gateway cities", "Direct access from the Americas"),
    "services": ("Touchpoints", "From arrival to departure"),
}

CTA_BANDS = {
    "home": "Bring your people, we'll bring the Caribbean.",
    "island": "Let's Create Your Caribbean Experience",
}

HERO = {
    "headline": "Your People, Our Home, Caribbean Connection",
    "lines": ["Your People.", "Our Home.", "Caribbean Connection."],
    "primary_cta": ("Explore Our Islands", "main.islands_index"),
    "secondary_cta": ("Submit an Event Brief", "main.connect"),
    "scenes": [
        ("arrival", "Arrival at SXM: private terminal welcome"),
        ("meeting", "Off-site meetings, island-side"),
        ("gala", "Gala dinner under the stars"),
        ("island", "The islands themselves, the reason we do this"),
    ],
}

# ---------------------------------------------------------------------------
# Homepage intro
# ---------------------------------------------------------------------------
HOME_INTRO = {
    "h2": "Inspired experiences and flawless execution for remarkable events across the Caribbean",
    "paragraphs": [
        "Welcome to Caribbean Incentive, where every experience is thoughtfully designed to bring people together, spark emotion, and leave a lasting impression.",
        "Born in the Caribbean and guided by deep local expertise, we create seamless incentive programs, corporate events, conferences, and group journeys across some of the region's most captivating islands.",
        "Whether you are planning an unforgettable incentive escape, a meaningful executive retreat, or a multi-island experience, our team brings every detail to life with warmth, creativity, and care.",
    ],
    "pull_quote": "Your people. Our home. One unforgettable Caribbean experience.",
}

# ---------------------------------------------------------------------------
# WHERE IT ALL BEGINS
# ---------------------------------------------------------------------------
WHERE_IT_ALL_BEGINS = {
    "kicker": "WHERE IT ALL BEGINS",
    "h2": "The Essence of Caribbean Incentive",
    "teaser_paragraphs": [
        "At Caribbean Incentive, we believe the most memorable events begin with a genuine connection to the destination, to its people, and to one another.",
        "As a boutique Caribbean DMC, we combine personal attention and creative flexibility with extensive destination knowledge and a trusted network of local partners.",
        "From the first idea to the final farewell, we become an extension of your team managing every detail with precision while making the entire experience feel effortless.",
    ],
    "full_h2": "Your vision, brought to life with Caribbean warmth",
    "full_paragraphs": [
        "At **Caribbean Incentive**, we create meaningful MICE programs and unforgettable group experiences across the Caribbean's most captivating islands.",
        "Our dedicated team combines international standards with genuine local insight. We understand the importance of culture, communication, and personal connection, allowing us to work seamlessly with clients and guests from around the world.",
        "From inspiring incentive journeys and executive retreats to conferences, celebrations, and multi-island programs, every experience is thoughtfully shaped around your people, your objectives, and the memories you want to create.",
        "With creativity, precision, and trusted relationships throughout the region, we take care of every detail, transforming ambitious ideas into beautifully executed Caribbean experiences.",
    ],
    "value_props": [
        {
            "title": "Exceptional Care",
            "body": "We approach every program with warmth and attention, delivering thoughtful service from the first conversation to the final farewell.",
        },
        {
            "title": "Creative Spirit",
            "body": "Every experience is individually designed, bringing together fresh ideas, authentic island character, and moments of genuine discovery.",
        },
        {
            "title": "Trusted Partnership",
            "body": "Transparency, reliability, and mutual respect are at the heart of every relationship we build.",
        },
        {
            "title": "Seamless Collaboration",
            "body": "We work as an extension of your team, bringing people, partners, and destinations together around one shared vision.",
        },
    ],
    "strengths": [
        "Deep, firsthand knowledge of the Caribbean and the distinctive character of each island we represent.",
        "A trusted network of exceptional local partners, unique venues, and memorable experiences across the region.",
        "One dedicated team coordinating every element of your program, from creative concept and logistics to production and on-site delivery.",
        "A flexible, personal approach shaped around your guests, your culture, and your objectives.",
        "The ability to create seamless single-island and multi-destination programs throughout the Caribbean.",
    ],
    "closer": "Where Caribbean warmth meets flawless execution, and every experience is made personally yours.",
}

# ---------------------------------------------------------------------------
# Explore Our Caribbean (homepage destination section)
# ---------------------------------------------------------------------------
EXPLORE_OUR_CARIBBEAN = {
    "h2": "Explore Our Caribbean",
    "lede": "Our reach extends across the Caribbean, from its iconic island destinations to its most secluded and authentic shores.",
    "pull_quote": "Rooted in the islands and guided by a genuine spirit of hospitality, we create exceptional Caribbean experiences that feel personal, seamless, and entirely your own.",
    "note": "Across every region, our unparalleled local knowledge and trusted partnerships transform your ambitions into unforgettable realities.",
    "closer": "Wherever the journey takes you, your guests will be welcomed with genuine Caribbean warmth.",
}

# ---------------------------------------------------------------------------
# DESIGNED AROUND YOU / WHAT WE DO
# ---------------------------------------------------------------------------
DESIGNED_AROUND_YOU = {
    "kicker": "WHAT WE DO",
    "h3": "Thoughtfully Created Around You",
    "teaser": "From seamless corporate gatherings to indulgent luxury escapes, our end-to-end destination management services across the Caribbean blend local authenticity with international sophistication.",
    "full_h2": "Crafted Exclusively for You",
    "full_paragraphs": [
        "Every experience we create begins with you: your vision, your objectives, and the way you want your guests to feel.",
        "From inspiring incentive journeys and executive retreats to conferences, corporate celebrations, and multi-island programs, our complete destination management services combine authentic Caribbean warmth with international standards of excellence.",
        "We listen carefully, think creatively, and manage every detail with precision. Accommodation, transportation, dining, activities, entertainment, production, and on-site coordination are thoughtfully brought together to create one seamless and memorable experience.",
    ],
}

# ---------------------------------------------------------------------------
# ENDLESS CREATIONS
# ---------------------------------------------------------------------------
ENDLESS_CREATIONS = {
    "kicker": "WHY CHOOSE THE CARIBBEAN",
    "h2": "Endless Creations",
    "teaser": "The Caribbean is far more than a destination: it is a vibrant collection of islands where natural beauty, rich cultures and modern elegance come together, creating endless possibilities for inspiration, discovery and connection.",
    "story_h3": "Your Caribbean Story",
    "story_paragraphs": [
        "Sail between hidden coves. Dine beneath the stars. Discover vibrant island traditions. Celebrate beside the sea. Connect with local communities. Share moments that your guests will remember long after they return home.",
        "Every Caribbean Incentive experience is shaped around your people, your purpose, and the feeling you want to create, bringing together authentic island character and refined execution.",
    ],
    "region_h2": "One Region. Endless Possibilities.",
    "region_paragraphs": [
        "The Caribbean is more than a collection of beautiful islands. It is a world of contrasts, where cultures meet, landscapes transform, and every journey carries its own rhythm.",
        "With direct air access from the United States, Canada, and Latin America, and effortless connections between neighboring islands by boat, the region offers extraordinary possibilities for incentive travel, corporate gatherings, and multi-destination programs.",
        "Here, business feels more human, celebrations feel more meaningful, and every shared experience brings people closer together.",
    ],
}

# ---------------------------------------------------------------------------
# TESTIMONIALS (homepage carousel) — demo placeholders pending real client
# quotes; swap freely, same shape: quote / name / role.
# ---------------------------------------------------------------------------
TESTIMONIALS = {
    "kicker": "WHAT OUR CLIENTS SAY",
    "h2": "Trusted to Deliver, Time After Time",
    "quotes": [
        {
            "quote": "From the first call to the final farewell dinner, Caribbean Incentive handled every detail as if it were their own event. Our executive retreat in Saint Martin felt effortless from our side, and unforgettable for our team.",
            "name": "Jordan Reyes",
            "role": "VP Events, Northwind Events Group",
        },
        {
            "quote": "We've run incentive programs across a dozen destinations, and this was the most seamless. Local knowledge, honest communication, and a team that genuinely cares how the week feels for our people.",
            "name": "Sade Okafor",
            "role": "Head of Corporate Retreats, Meridian Capital Partners",
        },
        {
            "quote": "They turned a fairly standard sales conference into something our team is still talking about. The gala on the beach in Grenada was the highlight of the year.",
            "name": "Priya Nair",
            "role": "Director of Marketing, Brightfield Logistics",
        },
    ],
}

# ---------------------------------------------------------------------------
# ENVISION YOUR EXPERIENCE
# ---------------------------------------------------------------------------
ENVISION = {
    "h2": "Your Vision, Brought to Life",
    "paragraphs": [
        "Every Caribbean program begins with an idea, a moment of connection, a sense of discovery, or an experience your guests will remember long after they return home.",
        "From the first arrival to the final farewell, explore how your vision could unfold through an inspiring sample itinerary, then create an initial planning estimate shaped around your destination, group and ambitions.",
    ],
    "itinerary_subhead": "What a five-day Caribbean incentive could look like",
    "estimator_subhead": "Create your planning estimate",
}

# ---------------------------------------------------------------------------
# LET'S CONNECT
# ---------------------------------------------------------------------------
CONNECT = {
    "h2": "Step beyond the expected. Beyond the familiar. Beyond the ordinary. Bring your people, we'll bring the Caribbean.",
    "paragraphs": [
        "Whether you envision an inspiring corporate event, an unforgettable incentive journey or an intimate executive retreat that reveals the true spirit of the Caribbean, we are here to bring your vision to life. Share your ambitions with us, and we will thoughtfully tailor every detail to reflect your objectives, your people and your unique idea of extraordinary.",
        "Let's create moments that remain long after the journey ends. Bring your people, we'll bring the Caribbean and make it happen!",
    ],
    "form_intro": "Please fill out the form below to share your inquiry with us. Whether it's MICE, luxury travel, or something uniquely yours, we are ready to create exceptional experiences together.",
}

# Social profiles — URLs TBC, client to supply. Drop an entry to hide its icon.
SOCIALS = [
    {"name": "Facebook", "url": "#", "icon": "facebook"},
    {"name": "Instagram", "url": "#", "icon": "instagram"},
    {"name": "LinkedIn", "url": "#", "icon": "linkedin"},
]

FOOTER = {
    "tagline": TAGLINE,
    "invite": "Bring your people, we'll bring the Caribbean.",
}
