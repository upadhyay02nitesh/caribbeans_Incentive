"""WhatsApp Business alerts for the three /lets-connect tabs.

Sends the same submission that services/mailer.py emails, as a WhatsApp message
to the business number, through the WhatsApp Cloud API (Meta). Stdlib only, so
nothing new to install.

Setup (Meta Business -> WhatsApp -> API Setup):
  WHATSAPP_TOKEN            permanent access token for the system user
  WHATSAPP_PHONE_ID         "Phone number ID" of the sending business number
  WHATSAPP_TO               number to alert, digits only with country code
  WHATSAPP_TEMPLATE         optional; approved template name (see below)

Message type matters. Meta only allows free-form text within 24 hours of the
recipient's last message to the business number. For a reliable alert that fires
at any hour, create an approved template whose body has five {{n}} placeholders
(kind, reference, name, company, contact) and set WHATSAPP_TEMPLATE to its name.
With no template configured this sends plain text, which is fine for testing and
inside that 24-hour window.

Leave the credentials blank and each alert is appended to
instance/whatsapp_outbox.jsonl instead — a submission is never lost and the
visitor never sees an error, matching the mail and Sellsy fallbacks.
"""

import json
import logging
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone

from flask import current_app

from services import mailer
from services.store import AST

logger = logging.getLogger(__name__)

KIND_LABELS = {
    "brief": "Event Brief",
    "rfp": "RFP Upload",
    "callback": "Callback Request",
}


def _config():
    cfg = current_app.config
    return {
        "token": cfg.get("WHATSAPP_TOKEN") or "",
        "phone_id": cfg.get("WHATSAPP_PHONE_ID") or "",
        "to": "".join(ch for ch in (cfg.get("WHATSAPP_TO") or cfg.get("WHATSAPP_NUMBER") or "") if ch.isdigit()),
        "template": cfg.get("WHATSAPP_TEMPLATE") or "",
        "lang": cfg.get("WHATSAPP_TEMPLATE_LANG") or "en_US",
        "version": cfg.get("WHATSAPP_API_VERSION") or "v21.0",
    }


# The alert carries what a phone screen can act on: who it is, how to reach
# them, and the shape of the request. Storage plumbing (object URLs, bucket
# paths, MIME types, byte counts) is filtered out exactly as it is in the
# e-mail — one rule, in services/mailer.py, for both channels.
HEADERS = {
    "brief": "📋 *New Event Brief*",
    "rfp": "📄 *New RFP Upload*",
    "callback": "📞 *New Callback Request*",
}
MAX_BODY = 3500        # WhatsApp allows 4096; leave room for long free text
MAX_FREE_TEXT = 700


def _text_body(kind, fields, reference):
    """A WhatsApp-formatted alert: header, who, how to reach them, the request."""
    stamp = datetime.now(AST).strftime("%d %b %Y · %H:%M AST")
    lines = [HEADERS.get(kind, "*New Inquiry*"), f"Ref {reference} · {stamp}", ""]

    name = mailer._lookup(fields, "Contact name", "Name")
    company = mailer._lookup(fields, "Company")
    email = mailer._lookup(fields, "E-mail", "Email")
    phone = mailer._lookup(fields, "Phone")

    if name or company:
        lines.append(f"*{name or company}*" + (f" — {company}" if name and company else ""))
    if email:
        lines.append(f"✉️ {email}")
    if phone:
        lines.append(f"📱 {phone}")
    if lines[-1]:
        lines.append("")

    for label, value in fields:
        key = str(label).lower()
        if value in (None, "", []) or key in mailer.INTERNAL_FIELDS or key in mailer.CONTACT_FIELDS:
            continue
        if key in mailer.DOWNLOAD_FIELDS or key == mailer.ATTACHMENT_FIELD:
            continue
        text = str(value).strip()
        if len(text) > 90 or "\n" in text:     # free text reads better on its own line
            lines.append(f"*{label}:*")
            lines.append(text[:MAX_FREE_TEXT] + ("…" if len(text) > MAX_FREE_TEXT else ""))
        else:
            lines.append(f"*{label}:* {text}")

    document = mailer._lookup(fields, "Attached file")
    if document:
        size = mailer._human_size(mailer._lookup(fields, "File size"))
        lines.append("")
        lines.append(f"📎 *Document:* {document}" + (f" ({size})" if size else ""))
        lines.append("_Attached to the e-mail; the file is in the admin dashboard._")

    lines.append("")
    lines.append("_Caribbean Incentive — website enquiry_")

    tidy = []                                  # never two blank lines in a row
    for line in lines:
        if line == "" and (not tidy or tidy[-1] == ""):
            continue
        tidy.append(line)
    return "\n".join(tidy)[:MAX_BODY]


def _template_params(kind, fields, reference):
    """Five positional values for the approved template body."""
    lookup = {name.lower(): value for name, value in fields if value not in (None, "", [])}
    name = lookup.get("contact name") or lookup.get("name") or "—"
    company = lookup.get("company") or "—"
    contact = lookup.get("e-mail") or lookup.get("phone") or "—"
    return [KIND_LABELS.get(kind, "Inquiry"), reference, str(name), str(company), str(contact)]


def _archive(kind, reference, payload, note):
    try:
        os.makedirs(current_app.instance_path, exist_ok=True)
        path = os.path.join(current_app.instance_path, "whatsapp_outbox.jsonl")
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "kind": kind,
                "reference": reference,
                "note": note,
                "payload": payload,
            }) + "\n")
    except Exception:
        logger.exception("Could not archive WhatsApp alert locally.")


def send_inquiry_alert(kind, fields, reference):
    """Send one submission to the business WhatsApp number. Returns True when sent."""
    cfg = _config()

    if cfg["template"]:
        payload = {
            "messaging_product": "whatsapp",
            "to": cfg["to"],
            "type": "template",
            "template": {
                "name": cfg["template"],
                "language": {"code": cfg["lang"]},
                "components": [{
                    "type": "body",
                    "parameters": [{"type": "text", "text": v} for v in _template_params(kind, fields, reference)],
                }],
            },
        }
    else:
        payload = {
            "messaging_product": "whatsapp",
            "to": cfg["to"],
            "type": "text",
            "text": {"preview_url": False, "body": _text_body(kind, fields, reference)},
        }

    if not (cfg["token"] and cfg["phone_id"] and cfg["to"]):
        _archive(kind, reference, payload, "WhatsApp not configured; archived only")
        logger.info("WhatsApp not configured — %s %s archived locally.", kind, reference)
        return False

    url = f"https://graph.facebook.com/{cfg['version']}/{cfg['phone_id']}/messages"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {cfg['token']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8", "replace")
        logger.info("WhatsApp alert sent for %s %s: %s", kind, reference, body[:200])
        _archive(kind, reference, payload, "sent")
        return True
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:400]
        logger.error("WhatsApp API rejected %s %s: %s %s", kind, reference, exc.code, detail)
        _archive(kind, reference, payload, f"HTTP {exc.code}: {detail}")
        return False
    except Exception:
        logger.exception("WhatsApp send failed for %s %s.", kind, reference)
        _archive(kind, reference, payload, "send failed; archived only")
        return False
