"""Site assistant: answers questions about Caribbean Incentive and runs the
planning estimator.

Two modes, chosen automatically:

* Claude mode (ANTHROPIC_API_KEY set) — Claude answers from a knowledge base
  built out of content/*.py at import time. Because the site is static that
  text never changes between requests, so it sits in a cached system prompt:
  after the first call it is billed at the cache-read rate. Numbers come only
  from the `estimate_trip` tool, which calls content.pricing.estimate() — the
  same function behind the on-page estimator — so the bot can never quote a
  figure the calculator wouldn't.

* Offline mode (no key, or the API is unreachable) — keyword answers built
  from the same content, plus the estimator for any message that names a
  group size and nights. The widget keeps working in a demo with no key.
"""

import logging
import os
import re

from content import experiences as experiences_content
from content import islands as islands_content
from content import pricing
from content import services as services_content
from content import site as site_content

logger = logging.getLogger(__name__)

MODEL = "claude-opus-5"
MAX_TURNS = 20            # messages of history accepted from the browser
MAX_CHARS = 1500          # per user message
MAX_TOOL_ROUNDS = 4       # tool calls per answer before we stop the loop

TIER_RATES = pricing.TIER_MULTIPLIER          # key -> tier multiplier
ADDON_KEYS = [key for key, _, _ in pricing.ADDONS]
ISLAND_SLUGS = list(pricing.ISLAND_RATE)
ISLAND_NAMES = dict(pricing.ISLAND_NAME)     # priced islands, incl. Saba (no page)


# ---------------------------------------------------------------------------
# Knowledge base — rendered once from content/, identical on every request so
# the cached prefix stays byte-stable.
# ---------------------------------------------------------------------------
def _join(paragraphs):
    return " ".join(p.replace("**", "") for p in paragraphs)


def _knowledge():
    s, lines = site_content, []
    add = lines.append

    add(f"# {s.BRAND} — {s.DESCRIPTOR}")
    add(f"Tagline: {s.TAGLINE}. Website: {s.DOMAIN}.")
    add(_join(s.HOME_INTRO["paragraphs"]))

    add("\n## Contact")
    add(f"Phone: {s.CONTACT['phone']}.")
    for label, window in s.CONTACT.get("hours", []):
        add(f"Hours, {label}: {window}.")
    for office in s.CONTACT.get("offices", []):
        add(f"Office — {office['name']}: {', '.join(office['lines'])}.")
    add(f"Email: {s.CONTACT['email']}.")
    add("Enquiries: the Let's Connect page has three options — submit an event brief, "
        "upload an RFP (PDF, Word or PowerPoint, max 10 MB), or request a callback.")

    add("\n## Where it all begins")
    add(_join(s.WHERE_IT_ALL_BEGINS["teaser_paragraphs"]))
    for v in s.WHERE_IT_ALL_BEGINS.get("value_props", []):
        add(f"- {v['title']}: {v['body']}")
    for strength in s.WHERE_IT_ALL_BEGINS.get("strengths", []):
        add(f"- {strength}")

    add("\n## What we do")
    add(_join(s.DESIGNED_AROUND_YOU["full_paragraphs"]))
    for category, items in services_content.SERVICE_CATEGORIES:
        add(f"{category}: {', '.join(items)}.")
    add("Services from arrival to departure: "
        + "; ".join(f"{title} ({desc})" for _, title, desc in services_content.JOURNEY) + ".")

    add("\n## Destinations (each has its own page)")
    for isle in islands_content.ISLANDS:
        add(f"### {isle['full_name']}")
        add(isle["headline"])
        if isle.get("intro"):
            add(isle["intro"])
        add(f"Access: {isle['access']}. Suited to: {isle.get('suited_to', '')}.")
        for mode, time, note in islands_content.CONNECTIONS.get(isle["slug"], []):
            add(f"Getting there: {mode}, {time} ({note}).")

    add("\n## Getting there (approximate flight times, planning estimates only)")
    add(f"Gateway cities: {', '.join(islands_content.ORIGINS)}.")
    for name, access, _slug in islands_content.GETTING_THERE:
        times = islands_content.APPROX_TIMES.get(name, {})
        add(f"- {name}: {access}. " + ", ".join(f"from {o} {t}" for o, t in times.items()) + ".")
    add(islands_content.GETTING_THERE_DISCLAIMER)

    add("\n## Experiences")
    add(experiences_content.EXPERIENCES_INTRO)
    for exp in experiences_content.EXPERIENCES:
        add(f"- {exp['title']}: {_join(exp['body'][:2])}")

    add("\n## Why the Caribbean")
    add(s.ENDLESS_CREATIONS["teaser"])

    add("\n## Planning estimator")
    add("Base rate per person, per night: "
        + "; ".join(f"{name} ${rate}" for _, name, rate in pricing.ISLAND_RATES) + ".")
    add("Tier multipliers: "
        + "; ".join(f"{name} (x{multiplier})" for _, name, _, multiplier in pricing.TIERS) + ".")
    add(f"The maths: (rate x nights x tier multiplier) x {pricing.SERVICE_FEE} on-site programme "
        "management fee, plus add-ons, gives the per-person total; multiplied by the group size it "
        "gives the programme total.")
    add("Add-ons (per person): " + "; ".join(f"{label} — ${p}" for _, label, p in pricing.ADDONS) + ".")
    add(pricing.ESTIMATOR_DISCLAIMER)
    return "\n".join(lines)


KNOWLEDGE = _knowledge()

SYSTEM_PROMPT = f"""You are the website assistant for {site_content.BRAND}, a boutique destination \
management company running incentive trips, executive retreats, conferences and group events \
across the Caribbean. Visitors are usually corporate event planners.

Answer from the knowledge base below. If it does not cover a question, say you don't have that \
detail and point them to the Let's Connect page, where the team replies personally. Never invent \
venues, prices, availability, dates or policies.

For any price or budget question, call the estimate_trip tool — do not calculate figures yourself. \
If the visitor hasn't given the island, group size, nights or tier, ask for what's missing in one \
short question, or use a sensible default and say which one you assumed. Always mention that the \
figure is a planning estimate that excludes airfare.

Keep replies short and warm: two to four sentences, or a brief list when comparing. Plain text \
only — no markdown headings or tables. When a page would help, name it: Explore Our Islands, \
Your Caribbean Journey, Envision Your Experience (the estimator), Connected to the Caribbean \
(getting there) or Let's Connect (enquiries).

<knowledge_base>
{KNOWLEDGE}
</knowledge_base>"""

ESTIMATE_TOOL = {
    "name": "estimate_trip",
    "description": (
        "Planning estimate for a group program, using the same calculator as the website. "
        "Returns per-person and total cost in USD, excluding airfare."
    ),
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "island": {"type": "string", "enum": ISLAND_SLUGS, "description": "Destination slug."},
            "group_size": {"type": "integer", "description": "Number of guests."},
            "nights": {"type": "integer", "description": "Number of nights."},
            "tier": {"type": "string", "enum": list(TIER_RATES), "description": "Accommodation tier."},
            "add_ons": {
                "type": "array",
                "items": {"type": "string", "enum": ADDON_KEYS},
                "description": "Optional per-person extras.",
            },
        },
        "required": ["island", "group_size", "nights", "tier", "add_ons"],
        "additionalProperties": False,
    },
}


def run_estimate(island, group_size, nights, tier, add_ons):
    """Validated call into content.pricing — shared by Claude and offline mode."""
    if island not in pricing.ISLAND_RATE:
        raise ValueError(f"Unknown island '{island}'.")
    if tier not in TIER_RATES:
        raise ValueError(f"Unknown tier '{tier}'.")
    group_size, nights = int(group_size), int(nights)
    if not (1 <= group_size <= 5000):
        raise ValueError("Group size must be between 1 and 5,000.")
    if not (1 <= nights <= 30):
        raise ValueError("Nights must be between 1 and 30.")
    add_ons = [a for a in add_ons if a in ADDON_KEYS]
    per_person, total = pricing.estimate(island, TIER_RATES[tier], nights, group_size, add_ons)
    return {
        "island": ISLAND_NAMES.get(island, island),
        "group_size": group_size,
        "nights": nights,
        "tier": tier,
        "add_ons": add_ons,
        "per_person_usd": per_person,
        "total_usd": total,
        "note": pricing.ESTIMATOR_DISCLAIMER,
    }


# ---------------------------------------------------------------------------
# Claude mode
# ---------------------------------------------------------------------------
_client = None


def _get_client():
    global _client
    if _client is None:
        import anthropic

        _client = anthropic.Anthropic(timeout=45.0, max_retries=2)
    return _client


def _claude_reply(history):
    import json

    client = _get_client()
    messages = list(history)

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            # Short, conversational answers: low effort keeps latency and cost down.
            output_config={"effort": "low"},
            # Frozen knowledge base first, cached across every visitor's requests.
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral", "ttl": "1h"}}],
            tools=[ESTIMATE_TOOL],
            messages=messages,
            # If a safety classifier declines, the API retries on a fallback model in the same call.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )

        if response.stop_reason == "refusal":
            return None
        if response.stop_reason != "tool_use":
            text = "".join(b.text for b in response.content if b.type == "text").strip()
            return text or None

        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            try:
                args = block.input if isinstance(block.input, dict) else json.loads(block.input)
                result = run_estimate(**args)
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(result)})
            except (TypeError, ValueError) as exc:
                results.append({"type": "tool_result", "tool_use_id": block.id,
                                "content": f"Error: {exc}", "is_error": True})
        messages.append({"role": "user", "content": results})

    logger.warning("Chat stopped after %d tool rounds.", MAX_TOOL_ROUNDS)
    return None


# ---------------------------------------------------------------------------
# Offline mode
# ---------------------------------------------------------------------------
ISLAND_ALIASES = {
    "saint-martin": ("saint martin", "st martin", "st. martin", "sint maarten", "sxm"),
    "st-barth": ("st barth", "st. barth", "saint barth", "st barts", "st barths", "saint-barth"),
    "anguilla": ("anguilla",),
    "british-virgin-islands": ("british virgin", "bvi", "virgin islands"),
    "dominica": ("dominica",),
    "grenada": ("grenada",),
    "barbados": ("barbados",),
}


def _find_island(text):
    for slug, aliases in ISLAND_ALIASES.items():
        if any(a in text for a in aliases):
            return slug
    return None


def _offline_estimate(text):
    pax = re.search(r"(\d{1,4})\s*(?:people|persons|pax|guests|attendees|participants|delegates)", text)
    nights = re.search(r"(\d{1,2})\s*(?:nights?|days?)", text)
    if not (pax and nights):
        return None
    tier = "ultra" if ("ultra" in text or "luxury" in text) else "premium" if "premium" in text else "classic"
    island = _find_island(text) or "saint-martin"
    add_ons = [k for k, words in {
        "transfers": ("transfer",), "boat": ("boat", "yacht", "cruise", "catamaran"),
        "gala": ("gala",), "decor": ("decor", "décor"), "entertainment": ("entertainment", "music", "band"),
        "concierge": ("concierge",),
    }.items() if any(w in text for w in words)]
    try:
        r = run_estimate(island, pax.group(1), nights.group(1), tier, add_ons)
    except ValueError as exc:
        return str(exc)
    extras = f" with {', '.join(r['add_ons'])}" if r["add_ons"] else ""
    assumed = "" if _find_island(text) else " (I assumed Saint Martin, since you did not name an island)"
    return (f"For {r['group_size']} guests, {r['nights']} nights, {r['tier'].title()} tier in "
            f"{r['island']}{assumed}{extras}: about ${r['per_person_usd']:,} per person, "
            f"${r['total_usd']:,} in total. That's a planning estimate excluding airfare — "
            f"the Envision Your Experience page lets you adjust it, and Let's Connect turns it into a proposal.")


def _offline_reply(message):
    text = message.lower()

    estimate = _offline_estimate(text)
    if estimate:
        return estimate

    if any(w in text for w in ("price", "cost", "budget", "estimate", "how much", "quote")):
        return ("I can give you a planning estimate. Tell me the island, group size, number of "
                "nights and tier (Classic, Premium or Ultra-luxury) — for example: '60 people, "
                "4 nights, Premium, Saint Martin with boat and gala'.")

    slug = _find_island(text)
    if slug:
        isle = islands_content.ISLAND_BY_SLUG[slug]
        return f"{isle['full_name']}: {isle['headline']} Access: {isle['access']}. Suited to {isle.get('suited_to', 'a range of programs').lower()}."

    if any(w in text for w in ("island", "destination", "where do you", "which place", "location")):
        names = ", ".join(i["name"] for i in islands_content.ISLANDS)
        return (f"We run programs across {names}. "
                "The Explore Our Islands page has a page for each.")

    if any(w in text for w in ("contact", "phone", "call", "email", "reach", "office", "address", "talk")):
        c = site_content.CONTACT
        offices = "; ".join(f"{o['name']}: {', '.join(o['lines'])}" for o in c.get("offices", []))
        return (f"You can call {c['phone']} or email {c['email']}. Offices — {offices}. "
                "Or use Let's Connect to send an event brief, upload an RFP or request a callback.")

    if any(w in text for w in ("fly", "flight", "getting there", "airport", "travel time", "how long")):
        return (f"Most programs arrive through Saint Martin, which has direct international flights from "
                f"{', '.join(islands_content.ORIGINS)}. Neighbouring islands are a short ferry or flight away. "
                "The Connected to the Caribbean page shows times from each gateway city.")

    if any(w in text for w in ("service", "what do you do", "offer", "mice", "conference", "incentive", "retreat")):
        cats = "; ".join(f"{c}: {', '.join(items[:4])}" for c, items in services_content.SERVICE_CATEGORIES)
        return f"We handle everything from arrival to departure. {cats}, and more — see Designed Around You."

    if any(w in text for w in ("experience", "activity", "activities", "team building", "things to do")):
        titles = ", ".join(e["title"] for e in experiences_content.EXPERIENCES)
        return f"Our experiences include {titles}. Your Caribbean Journey has the details."

    if any(w in text for w in ("hello", "hi ", "hey", "good morning", "good afternoon")) or text.strip() in ("hi", "hey"):
        return ("Hello! I can tell you about our islands, services and experiences, "
                "or give you a quick planning estimate. What are you planning?")

    return ("I can help with our islands, services, getting there, or a quick cost estimate. "
            "For anything else, the team replies personally through Let's Connect.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def clean_history(raw):
    """Keep only well-formed recent turns, starting with a user message."""
    history = []
    for m in (raw or [])[-MAX_TURNS:]:
        if not isinstance(m, dict):
            continue
        role, content = m.get("role"), m.get("content")
        if role in ("user", "assistant") and isinstance(content, str) and content.strip():
            history.append({"role": role, "content": content.strip()[:MAX_CHARS]})
    while history and history[0]["role"] != "user":
        history.pop(0)
    return history


def reply(raw_history):
    history = clean_history(raw_history)
    if not history or history[-1]["role"] != "user":
        return {"reply": "Ask me anything about our islands, services or a planning estimate.", "mode": "none"}

    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            text = _claude_reply(history)
            if text:
                return {"reply": text, "mode": "claude"}
        except Exception:
            logger.exception("Claude chat failed; answering offline.")

    return {"reply": _offline_reply(history[-1]["content"]), "mode": "offline"}
