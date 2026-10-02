"""Project Assistant — collects a corporate brief in conversation, then hands
it to the existing Let's Connect pipeline.

Two Gemini calls per turn, both through LangChain:

1. **Extract** — the whole transcript is re-read into a ProjectBrief schema
   (structured output, temperature 0). State lives in the transcript, not on
   the server and not in the browser: the client cannot inject field values,
   because every value is re-derived here from what was actually said.
2. **Ask** — one short, warm question for whatever is still missing, in the
   visitor's language.

When nothing required is missing the assistant stops and shows a summary with
the confirmation question. Nothing is submitted until the next request arrives
with ``confirm=True`` — an explicit click in the widget, never an inferred yes.
On confirmation the values are validated with the same EventBriefForm the
website form uses, then dispatched through services/leads.py.

No prices are quoted here: the site already has an estimator (Envision Your
Experience), and Ask Caraïbes can run it.
"""

import logging
import re
from typing import List, Optional

from pydantic import BaseModel, Field

from forms import BUDGET_RANGES, REQUEST_TYPES, EventBriefForm
from services import gemini
from services.chatbot import clean_history
from services.leads import dispatch_brief, reference_id

logger = logging.getLogger(__name__)

MAX_SUBMISSION_CHARS = 4000


class ProjectBrief(BaseModel):
    """What the visitor has told us so far. Every field may be missing."""

    language: str = Field("en", description="'fr' if the visitor writes in French, else 'en'.")
    company: Optional[str] = Field(None, description="Company or organisation name.")
    contact_name: Optional[str] = Field(None, description="Full name of the person writing.")
    email: Optional[str] = Field(None, description="Their e-mail address.")
    phone: Optional[str] = Field(None, description="Their phone number, with country code if given.")
    country: Optional[str] = Field(None, description="Country the group travels from.")
    destination: Optional[str] = Field(None, description="Caribbean island or destination they want.")
    event_type: Optional[str] = Field(None, description="Incentive, retreat, meeting, brand activation, etc.")
    participants: Optional[int] = Field(None, description="Number of participants.")
    dates: Optional[str] = Field(None, description="Preferred dates or travel window, as stated.")
    duration: Optional[str] = Field(None, description="Length of the programme, e.g. '4 nights'.")
    departure_location: Optional[str] = Field(None, description="City or airport the group departs from.")
    activities: List[str] = Field(default_factory=list, description="Activities or experiences asked for.")
    accommodation: Optional[str] = Field(None, description="Accommodation requirements.")
    transport: Optional[str] = Field(None, description="Transport or transfer requirements.")
    special_requirements: Optional[str] = Field(None, description="Dietary, accessibility, VIP or other needs.")
    budget: Optional[str] = Field(None, description="Budget, only if the visitor stated one.")


# Slots the brief cannot be submitted without, in the order we ask for them.
REQUIRED = [
    ("event_type", "the kind of event", "le type d'événement"),
    ("destination", "the destination", "la destination"),
    ("participants", "how many participants", "le nombre de participants"),
    ("dates", "the dates or travel window", "les dates ou la période"),
    ("contact_name", "your name", "votre nom"),
    ("company", "your company", "votre société"),
    ("email", "your e-mail", "votre e-mail"),
    ("phone", "your phone number", "votre numéro de téléphone"),
]

EXTRACT_SYSTEM = """Read the conversation between a visitor and the Caribbean Incentive \
assistant and return the project brief exactly as stated.

Rules:
- Only record what the visitor actually said. Never guess, complete or infer a value.
- Leave a field null if it has not been given. Do not use placeholders.
- participants must be a plain integer.
- Keep dates, budget and requirements in the visitor's own words.
- language: 'fr' if the visitor writes in French, otherwise 'en'."""

ASK_SYSTEM = """You are the Caribbean Incentive project assistant, helping a corporate client \
put together a brief for an event in the Caribbean.

- Reply in {language_name}.
- Warm, concise, professional: two or three sentences maximum, plain text, no markdown.
- Acknowledge briefly what they just told you, then ask for {ask_for}.
- Ask for at most two things in one message.
- Never invent or promise services, prices, availability or dates. Never quote a cost; if they \
ask, point them to the Envision Your Experience estimator or the Ask tab.
- Do not repeat questions already answered. Already collected: {collected}."""

REQUEST_TYPE_HINTS = [
    ("Corporate Incentive", ("incentive", "reward", "séminaire de motivation", "récompense")),
    ("Corporate Retreat", ("retreat", "offsite", "off-site", "retraite", "séminaire")),
    ("Meeting or Summit", ("meeting", "summit", "conference", "congrès", "convention", "réunion")),
    ("Brand Activation", ("activation", "launch", "lancement", "brand", "marque")),
]

BUDGET_BANDS = [
    ("Under $100k", 0, 100_000),
    ("$100k–250k", 100_000, 250_000),
    ("$250k–500k", 250_000, 500_000),
    ("$500k+", 500_000, float("inf")),
]


# ---------------------------------------------------------------------------
# Mapping the conversation onto the Let's Connect brief
# ---------------------------------------------------------------------------
def _request_type(event_type):
    text = (event_type or "").lower()
    for label, words in REQUEST_TYPE_HINTS:
        if any(w in text for w in words):
            return label
    return REQUEST_TYPES[1][0]  # Corporate Incentive


def _budget_band(budget):
    """Free text -> one of the form's ranges. Unknown or vague stays 'Not sure yet'."""
    if not budget:
        return BUDGET_RANGES[-1][0]
    text = budget.lower().replace(",", "").replace(" ", "")
    for label, _, _ in BUDGET_BANDS:
        if label.lower().replace(" ", "") in text:
            return label
    numbers = []
    for raw, suffix in re.findall(r"(\d+(?:\.\d+)?)\s*([kmKM]?)", text):
        value = float(raw) * {"k": 1_000, "m": 1_000_000}.get(suffix.lower(), 1)
        numbers.append(value)
    if not numbers:
        return BUDGET_RANGES[-1][0]
    top = max(numbers)
    for label, low, high in BUDGET_BANDS:
        if low <= top < high:
            return label
    return BUDGET_RANGES[-1][0]


def _message(brief):
    """Everything the form's free-text box would have carried."""
    parts = []
    add = parts.append
    if brief.event_type:
        add(f"Event type as described: {brief.event_type}.")
    if brief.destination:
        add(f"Destination: {brief.destination}.")
    if brief.duration:
        add(f"Duration: {brief.duration}.")
    if brief.departure_location:
        add(f"Departing from: {brief.departure_location}.")
    if brief.activities:
        add(f"Activities requested: {', '.join(brief.activities)}.")
    if brief.accommodation:
        add(f"Accommodation: {brief.accommodation}.")
    if brief.transport:
        add(f"Transport: {brief.transport}.")
    if brief.special_requirements:
        add(f"Special requirements: {brief.special_requirements}.")
    if brief.budget:
        add(f"Budget as stated: {brief.budget}.")
    add("Collected by the website project assistant.")
    return " ".join(parts)[:MAX_SUBMISSION_CHARS]


def to_values(brief):
    """ProjectBrief -> the dict services/leads.py and EventBriefForm expect."""
    return {
        "company": (brief.company or "").strip(),
        "contact_name": (brief.contact_name or "").strip(),
        "email": (brief.email or "").strip(),
        "phone": (brief.phone or "").strip(),
        "country": (brief.country or brief.departure_location or "Not specified").strip(),
        "request_type": _request_type(brief.event_type),
        "group_size": brief.participants,
        "preferred_dates": (brief.dates or "").strip()[:100],
        "budget": _budget_band(brief.budget),
        "message": _message(brief),
    }


def validate(brief):
    """Server-side validation with the website's own form. Returns error strings."""
    values = to_values(brief)
    form = EventBriefForm(formdata=None, data=values, meta={"csrf": False})
    if form.validate():
        return values, []
    errors = [f"{field.label.text}: {'; '.join(field.errors)}" for field in form if field.errors]
    return values, errors


def missing_slots(brief):
    return [slot for slot in REQUIRED if not getattr(brief, slot[0], None)]


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
SUMMARY_LABELS = {
    "en": [("Event", "event_type"), ("Destination", "destination"), ("Participants", "participants"),
           ("Dates", "dates"), ("Duration", "duration"), ("Departing from", "departure_location"),
           ("Activities", "activities"), ("Accommodation", "accommodation"), ("Transport", "transport"),
           ("Special requirements", "special_requirements"), ("Budget", "budget"),
           ("Company", "company"), ("Contact", "contact_name"), ("E-mail", "email"), ("Phone", "phone")],
    "fr": [("Événement", "event_type"), ("Destination", "destination"), ("Participants", "participants"),
           ("Dates", "dates"), ("Durée", "duration"), ("Départ de", "departure_location"),
           ("Activités", "activities"), ("Hébergement", "accommodation"), ("Transport", "transport"),
           ("Demandes particulières", "special_requirements"), ("Budget", "budget"),
           ("Société", "company"), ("Contact", "contact_name"), ("E-mail", "email"), ("Téléphone", "phone")],
}
CONFIRM_QUESTION = {
    "en": "Here is your project brief. Would you like me to submit it to Caraïbes Incentive?",
    "fr": "Voici votre brief de projet. Souhaitez-vous que je l'envoie à Caraïbes Incentive ?",
}
SUBMITTED = {
    "en": ("Your brief is with the Caraïbes Incentive team — reference {ref}. "
           "A confirmation is on its way to {email}, and we will come back to you personally within one business day."),
    "fr": ("Votre brief a bien été transmis à l'équipe Caraïbes Incentive — référence {ref}. "
           "Une confirmation part vers {email}, et nous revenons vers vous personnellement sous un jour ouvré."),
}
FIX = {
    "en": "Almost there — I still need this corrected before I can submit: {errors}",
    "fr": "Presque — il me manque encore ceci avant de pouvoir envoyer : {errors}",
}
UNAVAILABLE = {
    "en": ("I can't build your brief right now. The Let's Connect page takes the same details and "
           "reaches the team directly."),
    "fr": ("Je ne peux pas constituer votre brief pour le moment. La page Let's Connect recueille les "
           "mêmes informations et joint directement l'équipe."),
}


def summary_text(brief):
    lang = "fr" if brief.language == "fr" else "en"
    lines = []
    for label, attr in SUMMARY_LABELS[lang]:
        value = getattr(brief, attr, None)
        if not value:
            continue
        if isinstance(value, list):
            value = ", ".join(value)
        lines.append(f"{label}: {value}")
    return "\n".join(lines)


def _brief_dict(brief):
    """What the widget renders in the summary card — no internal mapping leaked."""
    lang = "fr" if brief.language == "fr" else "en"
    items = []
    for label, attr in SUMMARY_LABELS[lang]:
        value = getattr(brief, attr, None)
        if not value:
            continue
        items.append({"label": label, "value": ", ".join(value) if isinstance(value, list) else str(value)})
    return items


# ---------------------------------------------------------------------------
# Gemini calls
# ---------------------------------------------------------------------------
def _extract(history):
    llm = gemini.chat_model(temperature=0.0)
    if llm is None:
        return None
    from langchain_core.messages import SystemMessage

    transcript = "\n".join(
        f"{'Visitor' if m['role'] == 'user' else 'Assistant'}: {m['content']}" for m in history
    )
    model = llm.with_structured_output(ProjectBrief)
    return model.invoke([SystemMessage(content=EXTRACT_SYSTEM), ("human", transcript)])


def _next_question(history, brief, missing):
    lang = "fr" if brief.language == "fr" else "en"
    ask_for = ", ".join(slot[2] if lang == "fr" else slot[1] for slot in missing[:2])
    collected = summary_text(brief) or ("rien pour le moment" if lang == "fr" else "nothing yet")

    llm = gemini.chat_model(temperature=0.3)
    if llm is None:
        return None
    from langchain_core.messages import SystemMessage

    system = ASK_SYSTEM.format(
        language_name="French" if lang == "fr" else "English",
        ask_for=ask_for,
        collected=collected.replace("\n", "; "),
    )
    messages = [SystemMessage(content=system)] + gemini.to_messages(history)
    return gemini.response_text(llm.invoke(messages)) or None


def _fallback_question(brief, missing):
    lang = "fr" if brief.language == "fr" else "en"
    ask_for = ", ".join(slot[2] if lang == "fr" else slot[1] for slot in missing[:2])
    if lang == "fr":
        return f"Merci. Pouvez-vous me préciser {ask_for} ?"
    return f"Thank you. Could you tell me {ask_for}?"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def respond(raw_history, confirm=False, request=None):
    """One turn of the project conversation.

    Returns {reply, mode, ready, brief, reference?} — `ready` means the summary
    has been shown and a confirmed submission would be accepted.
    """
    history = clean_history(raw_history)
    lang = "fr" if _looks_french(history) else "en"

    if not gemini.available():
        return {"reply": UNAVAILABLE[lang], "mode": "project", "ready": False, "brief": []}

    if not history:
        return {"reply": _opening(lang), "mode": "project", "ready": False, "brief": []}

    try:
        brief = _extract(history)
    except Exception:
        logger.exception("Project assistant extraction failed.")
        return {"reply": UNAVAILABLE[lang], "mode": "project", "ready": False, "brief": []}

    if brief is None:
        return {"reply": UNAVAILABLE[lang], "mode": "project", "ready": False, "brief": []}

    lang = "fr" if brief.language == "fr" else "en"
    missing = missing_slots(brief)

    # ---------------------------------------------------------------- submit
    if confirm:
        if missing:
            return {"reply": _fallback_question(brief, missing), "mode": "project",
                    "ready": False, "brief": _brief_dict(brief)}
        values, errors = validate(brief)
        if errors:
            return {"reply": FIX[lang].format(errors="; ".join(errors)), "mode": "project",
                    "ready": True, "brief": _brief_dict(brief)}
        values["reference"] = reference_id("BRF")
        try:
            reference = dispatch_brief(values, request=request, source="chat")
        except Exception:
            logger.exception("Project assistant could not dispatch the brief.")
            return {"reply": UNAVAILABLE[lang], "mode": "project", "ready": True,
                    "brief": _brief_dict(brief)}
        return {"reply": SUBMITTED[lang].format(ref=reference, email=values["email"]),
                "mode": "project", "ready": False, "submitted": True,
                "reference": reference, "brief": _brief_dict(brief)}

    # ------------------------------------------------------------ keep going
    if missing:
        try:
            question = _next_question(history, brief, missing)
        except Exception:
            logger.exception("Project assistant question failed.")
            question = None
        return {"reply": question or _fallback_question(brief, missing), "mode": "project",
                "ready": False, "brief": _brief_dict(brief)}

    # ----------------------------------------------------- summary + confirm
    values, errors = validate(brief)
    if errors:
        return {"reply": FIX[lang].format(errors="; ".join(errors)), "mode": "project",
                "ready": False, "brief": _brief_dict(brief)}
    return {"reply": f"{summary_text(brief)}\n\n{CONFIRM_QUESTION[lang]}", "mode": "project",
            "ready": True, "brief": _brief_dict(brief)}


FRENCH_MARKERS = (" le ", " la ", " les ", " nous ", " vous ", "bonjour", "merci", "souhait",
                  "événement", "evenement", "séminaire", "seminaire", "personnes", "entreprise")


def _looks_french(history):
    text = " ".join(m["content"] for m in history if m["role"] == "user").lower()
    return sum(marker in f" {text} " for marker in FRENCH_MARKERS) >= 2


def _opening(lang):
    if lang == "fr":
        return ("Avec plaisir. Parlez-moi de votre projet : quel type d'événement, pour combien de "
                "personnes, et à quelle période ?")
    return ("Happy to help. Tell me about your project: what kind of event, for how many people, "
            "and roughly when?")
