"""One way into the Let's Connect pipeline for an event brief.

The /inquiry/brief form and the chat Project Assistant both end here, so a
brief raised in the chatbot is indistinguishable downstream from one typed on
the page: same reference format, same e-mail, WhatsApp alert, database row,
Sellsy opportunity and visitor conversion.
"""

import logging
import os
from datetime import datetime, timezone

from services.mailer import send_inquiry
from services.sellsy import send_to_sellsy
from services.store import save_inquiry
from services.visitors import identify
from services.whatsapp import send_inquiry_alert

logger = logging.getLogger(__name__)


def reference_id(prefix):
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%y%m%d')}-{os.urandom(2).hex().upper()}"


def brief_fields(values):
    """The field list, in the order every channel renders it."""
    return [
        ("Company", values.get("company")),
        ("Contact name", values.get("contact_name")),
        ("E-mail", values.get("email")),
        ("Phone", values.get("phone")),
        ("Country", values.get("country")),
        ("Type of request", values.get("request_type")),
        ("Group size", values.get("group_size")),
        ("Preferred dates", values.get("preferred_dates")),
        ("Average budget", values.get("budget")),
        ("About the event", values.get("message")),
    ]


def dispatch_brief(values, request=None, source="form"):
    """Send one event brief everywhere it needs to go. Returns the reference."""
    reference = values.get("reference") or reference_id("BRF")
    fields = brief_fields(values)

    emailed = send_inquiry("brief", fields, reference, reply_to=values.get("email"),
                           ack_to=values.get("email"), ack_name=values.get("contact_name"))
    whatsapped = send_inquiry_alert("brief", fields, reference)
    save_inquiry("brief", fields, reference, emailed, whatsapped, request)
    send_to_sellsy("brief", reference, fields,
                   channel="Chat assistant (Project Assistant)" if source == "chat" else "Let's Connect form",
                   company=values.get("company"), contact_name=values.get("contact_name"),
                   email=values.get("email"), phone=values.get("phone"),
                   country=values.get("country"), request_type=values.get("request_type"),
                   group_size=values.get("group_size"), budget=values.get("budget"))
    identify("brief", reference, fields)
    logger.info("Brief %s dispatched (source=%s, emailed=%s).", reference, source, emailed)
    return reference
