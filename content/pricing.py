"""Planning estimate model — MODULE 5.

Client-supplied model (September 2026 update):

    (base rate x nights x tier multiplier) x 1.12 + add-ons = per person
    per person x group size                                 = program total

The 1.12 is a flat 12% on-site program management fee, applied to every
calculation before the per-person add-ons are added.

Verified worked example: Saint Martin, 60 people, 4 nights, Premium,
transfers + boat + gala + décor -> $1,958 per person, $117,480 total.
"""

SERVICE_FEE = 1.12  # flat 12% on-site programme management fee

# Base rate per person, per night (USD). Site order, Saint Martin first; Saba is priced
# but has no destination page, so it appears in the estimator only.
ISLAND_RATES = [
    ("saint-martin", "Saint Martin / Sint Maarten", 280),
    ("anguilla", "Anguilla", 520),
    ("st-barth", "St Barths", 650),
    ("british-virgin-islands", "British Virgin Islands", 310),
    ("saba", "Saba", 320),
    ("dominica", "Dominica", 280),
    ("grenada", "Grenada", 280),
    ("barbados", "Barbados", 290),
]
ISLAND_RATE = {slug: rate for slug, _, rate in ISLAND_RATES}
ISLAND_NAME = {slug: name for slug, name, _ in ISLAND_RATES}
DEFAULT_RATE = ISLAND_RATE["saint-martin"]

# (key, name, description, multiplier) — Premium is the default selection.
TIERS = [
    ("essential", "Essential", "quality properties, core experiences", 1.0),
    ("premium", "Premium", "upgraded properties, private experiences", 1.35),
    ("signature", "Signature", "villas, exclusive access", 1.8),
]
TIER_MULTIPLIER = {key: multiplier for key, _, _, multiplier in TIERS}

# Flat per person, added after the service fee.
ADDONS = [
    ("transfers", "Ground & inter-island transfers", 35),
    ("boat", "Private boat charter / day cruise", 80),
    ("gala", "Gala dinner & themed event", 100),
    ("decor", "Décor & event production", 50),
    ("excursions", "Guided excursions / activities", 60),
]

ESTIMATOR_DISCLAIMER = (
    "Base package includes accommodation, group dining and core activities, plus a "
    "12% on-site program management fee. Add-ons above are priced per person on top. "
    "Excludes airfare. Final pricing depends on dates and availability."
)

ESTIMATOR_COPY = {
    "heading": "Get a ballpark number in 30 seconds.",
    "sub": "Tap a destination above, or set your own: the estimate updates live.",
    "cta": "TURN THIS INTO A REAL PROPOSAL",
}


def estimate(island, tier_multiplier, nights, pax, addon_keys):
    """Per-person and program totals. Mirrored exactly in static/js/estimator.js."""
    addon_total = sum(price for key, _, price in ADDONS if key in addon_keys)
    rate = ISLAND_RATE.get(island, DEFAULT_RATE)
    per_person = round(rate * nights * tier_multiplier * SERVICE_FEE + addon_total)
    return per_person, per_person * pax
