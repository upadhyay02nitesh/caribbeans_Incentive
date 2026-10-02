"""Outbound email for the three /lets-connect tabs.

Uses stdlib smtplib so the only configuration needed is a Gmail account plus an
app password (Google Account -> Security -> 2-Step Verification -> App passwords).
Set MAIL_USERNAME / MAIL_PASSWORD in .env and it sends; leave them blank and the
submission is written to instance/submissions.jsonl instead, exactly as before —
the site never reports failure to the visitor because email is unavailable.

Two messages go out per submission:
  1. the notification to INQUIRY_RECIPIENT (the team), with the RFP attached
  2. a short acknowledgement to the person who submitted, carrying the reference
"""

import json
import logging
import os
import smtplib
from urllib.parse import quote
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import formataddr, formatdate

from flask import current_app

from content import site as site_content
from services.store import AST

from services import graph_mail

logger = logging.getLogger(__name__)

BRAND = "Caribbean Incentive"
INK = "#17203B"
DEEP = "#0E1528"
GOLD = "#C68C3A"
GOLD_SOFT = "#E2B062"
IVORY = "#FBF7F0"
SAND = "#F3E9D8"
MUTED = "#77808B"

# (section label, notification heading, phrase used in the acknowledgement)
KIND_LABELS = {
    "brief": ("Event Brief", "New event brief", "event brief"),
    "rfp": ("RFP Upload", "New RFP upload", "RFP"),
    "callback": ("Callback Request", "New callback request", "callback request"),
}
FALLBACK_LABEL = ("Inquiry", "New inquiry", "enquiry")

# ---------------------------------------------------------------------------
# HTML template
#
# Table-based, 600px, inline styles only — the layout Outlook/Gmail/Apple Mail
# all render the same. The palette and type mirror the website: deep-ocean navy
# ground, ivory paper, champagne gold accents, serif display over sans body.
#
# What goes in an email is *only* what a human needs to answer the enquiry.
# Storage plumbing (object URLs, bucket paths, MIME types, byte counts) stays
# in the database and Sellsy and is never printed here — the document travels
# as an attachment, with at most one signed download button.
# ---------------------------------------------------------------------------

# Labels whose values are machinery, not message. Matched case-insensitively.
INTERNAL_FIELDS = {"file url", "file path", "file type", "file size", "storage path", "bucket"}
# Pulled out of the detail list and rendered in the contact panel instead.
CONTACT_FIELDS = {"company", "contact name", "name", "e-mail", "email", "phone"}
DOWNLOAD_FIELDS = {"download (7 days)", "download link", "signed url"}
ATTACHMENT_FIELD = "attached file"

SIGNATURE_NAME = "Karishma Singh"
SIGNATURE_ROLE = site_content.CONTACT["partner"]["eyebrow"]
# One source of truth: the footer shows whatever /lets-connect shows.
OFFICE_ADDRESS = site_content.CONTACT["address"]
OFFICE_PHONE = site_content.CONTACT["phone"]
OFFICE_EMAIL = site_content.CONTACT["email"]
TAGLINE = site_content.TAGLINE

SANS = "'Helvetica Neue',Helvetica,Arial,sans-serif"
SERIF = "Georgia,'Times New Roman',serif"
LINE = "#E8E1D4"
BODY = "#4A5460"


def _esc(value):
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _text(value):
    """Escaped, line breaks preserved — never a bare URL."""
    return _esc(value).replace(chr(10), "<br>")


def _lookup(fields, *labels):
    wanted = {label.lower() for label in labels}
    for label, value in fields:
        if str(label).lower() in wanted and value not in (None, "", []):
            return str(value)
    return ""


def _human_size(value):
    try:
        size = float(value)
    except (TypeError, ValueError):
        return ""
    if size < 1024:
        return f"{size:,.0f} bytes"
    for unit in ("KB", "MB", "GB"):
        size /= 1024
        if size < 1024 or unit == "GB":
            return f"{size:,.1f} {unit}"
    return ""


def _button(href, label):
    return (
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
        f'<td bgcolor="{GOLD_SOFT}" style="background:{GOLD_SOFT};border-radius:2px;">'
        f'<a href="{_esc(href)}" style="display:inline-block;padding:14px 26px;font:600 11px/1 {SANS};'
        f'letter-spacing:.18em;text-transform:uppercase;color:{INK};text-decoration:none;">{_esc(label)}</a>'
        f'</td></tr></table>'
    )


def _rows_html(fields):
    """The detail list: label column, value column, hairline between rows."""
    rows = []
    for label, value in fields:
        key = str(label).lower()
        if value in (None, "", []) or key in INTERNAL_FIELDS or key in CONTACT_FIELDS:
            continue
        if key in DOWNLOAD_FIELDS or key == ATTACHMENT_FIELD:
            continue
        rows.append(
            f'<tr>'
            f'<td style="padding:14px 16px 14px 0;border-bottom:1px solid {LINE};font:600 10px/1.5 {SANS};'
            f'letter-spacing:.16em;text-transform:uppercase;color:{MUTED};width:36%;vertical-align:top;">{_esc(label)}</td>'
            f'<td style="padding:14px 0;border-bottom:1px solid {LINE};font:400 15px/1.6 {SANS};'
            f'color:{INK};vertical-align:top;">{_text(value)}</td>'
            f'</tr>'
        )
    return "".join(rows)


def _contact_panel(fields):
    """Who to answer, on a navy card — the first thing the team needs."""
    name = _lookup(fields, "Contact name", "Name")
    company = _lookup(fields, "Company")
    email = _lookup(fields, "E-mail", "Email")
    phone = _lookup(fields, "Phone")
    if not (name or company or email or phone):
        return ""

    links = []
    if email:
        links.append(f'<a href="mailto:{_esc(email)}" style="color:{GOLD_SOFT};text-decoration:none;">{_esc(email)}</a>')
    if phone:
        tel = "".join(ch for ch in phone if ch.isdigit() or ch == "+")
        links.append(f'<a href="tel:{_esc(tel)}" style="color:{GOLD_SOFT};text-decoration:none;">{_esc(phone)}</a>')
    contact_line = " &nbsp;&middot;&nbsp; ".join(links)

    heading = _esc(name or company)
    sub = _esc(company) if (name and company) else ""
    sub_html = (f'<div style="margin-top:3px;font:400 13px/1.5 {SANS};color:rgba(251,247,240,.66);">{sub}</div>'
                if sub else "")
    links_html = (f'<div style="margin-top:12px;font:400 14px/1.6 {SANS};">{contact_line}</div>'
                  if contact_line else "")
    return f"""
      <tr><td style="padding:0 40px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{INK}"
               style="background:{INK};border-radius:3px;">
          <tr><td style="padding:22px 24px;">
            <div style="font:600 10px/1.4 {SANS};letter-spacing:.2em;text-transform:uppercase;color:{GOLD_SOFT};">From</div>
            <div style="margin-top:8px;font:400 21px/1.3 {SERIF};color:{IVORY};">{heading}</div>
            {sub_html}
            {links_html}
          </td></tr>
        </table>
      </td></tr>"""


def _attachment_block(fields):
    """One sand chip for the document, plus a single download button if signed."""
    filename = _lookup(fields, "Attached file")
    if not filename:
        return ""
    size = _human_size(_lookup(fields, "File size"))
    download = ""
    for label, value in fields:
        if str(label).lower() in DOWNLOAD_FIELDS and value:
            download = str(value)
            break

    meta = " &nbsp;&middot;&nbsp; ".join(part for part in (size, "attached to this email") if part)
    button = f'<div style="margin-top:16px;">{_button(download, "Download document")}</div>' \
        if download.startswith(("http://", "https://")) else ""
    return f"""
      <tr><td style="padding:26px 40px 0;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{SAND}"
               style="background:{SAND};border-radius:3px;">
          <tr><td style="padding:20px 22px;border-left:3px solid {GOLD_SOFT};">
            <div style="font:600 10px/1.4 {SANS};letter-spacing:.2em;text-transform:uppercase;color:{GOLD};">Document</div>
            <div style="margin-top:8px;font:600 15px/1.5 {SANS};color:{INK};word-break:break-word;">{_esc(filename)}</div>
            <div style="margin-top:4px;font:400 13px/1.5 {SANS};color:{MUTED};">{meta}</div>
            {button}
          </td></tr>
        </table>
      </td></tr>"""


def _shell(preheader, body_html):
    """Masthead, gold rule, body, signature footer — shared by both messages."""
    year = datetime.now().year
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="x-apple-disable-message-reformatting">
<meta name="color-scheme" content="light only">
<meta name="supported-color-schemes" content="light only">
<title>{BRAND}</title>
</head>
<body style="margin:0;padding:0;background:{SAND};-webkit-font-smoothing:antialiased;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;mso-hide:all;">{_esc(preheader)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{SAND}" style="background:{SAND};">
  <tr><td align="center" style="padding:36px 14px;">
    <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"
           style="width:600px;max-width:100%;background:{IVORY};border-radius:4px;overflow:hidden;
                  box-shadow:0 26px 60px -34px rgba(14,21,40,.55);">

      <tr><td bgcolor="{INK}" style="background:{INK};padding:34px 40px 30px;">
        <div style="font:400 23px/1.2 {SERIF};color:{IVORY};">{BRAND}</div>
        <div style="margin-top:8px;font:600 9.5px/1.4 {SANS};letter-spacing:.3em;text-transform:uppercase;color:{GOLD_SOFT};">
          Boutique Caribbean DMC
        </div>
      </td></tr>
      <tr><td bgcolor="{GOLD}" style="height:3px;line-height:3px;font-size:0;background:{GOLD};
               background-image:linear-gradient(90deg,{GOLD_SOFT},{GOLD},#E9745B);">&nbsp;</td></tr>
{body_html}
      <tr><td bgcolor="{DEEP}" style="background:{DEEP};padding:28px 40px;">
        <div style="font:italic 400 15px/1.4 {SERIF};color:{GOLD_SOFT};">{TAGLINE}</div>
        <div style="margin-top:14px;font:400 12.5px/1.8 {SANS};color:rgba(251,247,240,.66);">
          {OFFICE_ADDRESS}<br>
          <a href="tel:{OFFICE_PHONE.replace(' ', '')}" style="color:rgba(251,247,240,.66);text-decoration:none;">{OFFICE_PHONE}</a>
          &nbsp;&middot;&nbsp;
          <a href="mailto:{OFFICE_EMAIL}" style="color:rgba(251,247,240,.66);text-decoration:none;">{OFFICE_EMAIL}</a>
        </div>
        <div style="margin-top:14px;font:400 11px/1.5 {SANS};color:rgba(251,247,240,.38);">{BRAND} &copy; {year}</div>
      </td></tr>

    </table>
  </td></tr>
</table>
</body></html>"""


def _notification_html(kind, fields, reference):
    title, heading, _ = KIND_LABELS.get(kind, FALLBACK_LABEL)
    stamp = datetime.now(AST).strftime("%d %B %Y &middot; %H:%M AST")
    sender = _lookup(fields, "Contact name", "Name") or _lookup(fields, "Company") or "a new enquiry"
    email = _lookup(fields, "E-mail", "Email")

    reply = ""
    if email:
        href = f"mailto:{email}?subject={quote(f'{BRAND} enquiry {reference}')}"
        reply = f'\n      <tr><td style="padding:30px 40px 0;">{_button(href, "Reply to sender")}</td></tr>'

    rows = _rows_html(fields)
    details = f"""
      <tr><td style="padding:26px 40px 0;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
               style="border-top:1px solid {LINE};">{rows}</table>
      </td></tr>""" if rows else ""

    return _shell(
        f"{heading} from {sender} — {reference}",
        f"""
      <tr><td style="padding:38px 40px 0;">
        <div style="font:600 10px/1.4 {SANS};letter-spacing:.22em;text-transform:uppercase;color:{GOLD};">{_esc(title)}</div>
        <h1 style="margin:12px 0 0;font:400 30px/1.2 {SERIF};color:{INK};">{_esc(heading)}</h1>
        <div style="margin-top:10px;font:400 13px/1.6 {SANS};color:{MUTED};">
          {stamp} &nbsp;&middot;&nbsp; Reference <span style="color:{INK};font-weight:600;">{_esc(reference)}</span>
        </div>
      </td></tr>
      <tr><td style="height:26px;line-height:26px;font-size:0;">&nbsp;</td></tr>
{_contact_panel(fields)}{details}{_attachment_block(fields)}{reply}
      <tr><td style="padding:30px 40px 36px;font:400 12.5px/1.7 {SANS};color:{MUTED};">
        Sent from the enquiry form on the {BRAND} website. Replying to this message reaches the sender directly.
      </td></tr>"""
    )


def _ack_html(name, kind, reference):
    _, _, phrase = KIND_LABELS.get(kind, FALLBACK_LABEL)
    steps = [
        ("01", "It is already with us",
         f"Your {phrase} went straight to our team in Saint-Martin — no queue, no call centre."),
        ("02", "A considered reply",
         "Expect a personal response within one business day, with first thoughts on what is possible."),
        ("03", "We shape it together",
         "From there we build the programme around your people, your objectives and your dates."),
    ]
    step_html = "".join(
        f"""
          <tr>
            <td width="46" style="padding:14px 0;vertical-align:top;font:400 15px/1.6 {SERIF};color:{GOLD};">{n}</td>
            <td style="padding:14px 0;border-bottom:1px solid {LINE};">
              <div style="font:600 14px/1.5 {SANS};color:{INK};">{_esc(t)}</div>
              <div style="margin-top:4px;font:400 14px/1.65 {SANS};color:{BODY};">{_esc(b)}</div>
            </td>
          </tr>"""
        for n, t, b in steps
    )

    return _shell(
        f"We have your {phrase} — reference {reference}",
        f"""
      <tr><td style="padding:40px 40px 0;">
        <h1 style="margin:0;font:400 30px/1.25 {SERIF};color:{INK};">Thank you, {_esc(name)}</h1>
        <p style="margin:16px 0 0;font:400 16px/1.7 {SANS};color:{BODY};">
          We have your {_esc(phrase)} and it is with our team now. Your reference is
          <strong style="color:{INK};">{_esc(reference)}</strong> — keep it to hand; we will quote it in every reply.
        </p>
      </td></tr>

      <tr><td style="padding:28px 40px 0;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
               style="border-top:1px solid {LINE};">{step_html}</table>
      </td></tr>

      <tr><td style="padding:30px 40px 0;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{SAND}"
               style="background:{SAND};border-radius:3px;">
          <tr><td style="padding:24px;border-left:3px solid {GOLD_SOFT};">
            <div style="font:italic 400 19px/1.45 {SERIF};color:{INK};">
              &ldquo;Personal attention from the first conversation to the final farewell.&rdquo;
            </div>
            <div style="margin-top:14px;font:600 11px/1.4 {SANS};letter-spacing:.16em;text-transform:uppercase;color:{GOLD};">
              {SIGNATURE_NAME}
            </div>
            <div style="margin-top:4px;font:400 13px/1.5 {SANS};color:{MUTED};">{SIGNATURE_ROLE}, {BRAND}</div>
          </td></tr>
        </table>
      </td></tr>

      <tr><td style="padding:30px 40px 40px;">
        {_button(f"mailto:{OFFICE_EMAIL}?subject={quote(reference)}", "Add to your enquiry")}
      </td></tr>"""
    )


def _plain(fields, reference):
    """Plain-text twin — same substance, no links, no storage plumbing."""
    lines = [f"{BRAND}", f"Reference: {reference}", ""]
    for label, value in fields:
        key = str(label).lower()
        if value in (None, "", []) or key in INTERNAL_FIELDS or key in DOWNLOAD_FIELDS:
            continue
        if key == ATTACHMENT_FIELD:
            size = _human_size(_lookup(fields, "File size"))
            lines.append(f"Document: {value}" + (f" ({size}, attached)" if size else " (attached)"))
            continue
        lines.append(f"{label}: {value}")
    lines += ["", TAGLINE]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sending
# ---------------------------------------------------------------------------
def _config():
    cfg = current_app.config
    return {
        "server": cfg.get("MAIL_SERVER") or "smtp.gmail.com",
        "port": int(cfg.get("MAIL_PORT") or 587),
        "tls": bool(cfg.get("MAIL_USE_TLS", True)),
        "username": cfg.get("MAIL_USERNAME") or "",
        "password": cfg.get("MAIL_PASSWORD") or "",
        "sender": cfg.get("MAIL_DEFAULT_SENDER") or cfg.get("MAIL_USERNAME") or "",
        "recipient": cfg.get("INQUIRY_RECIPIENT") or "",
    }


def _archive(kind, fields, reference, note):
    """Local fallback so a submission is never lost when SMTP is unavailable."""
    try:
        path = os.path.join(current_app.instance_path, "submissions.jsonl")
        os.makedirs(current_app.instance_path, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "kind": kind,
                "reference": reference,
                "note": note,
                "fields": {label: value for label, value in fields},
            }) + "\n")
    except Exception:
        logger.exception("Could not archive submission locally.")


def send_inquiry(kind, fields, reference, reply_to=None, ack_to=None, ack_name=None, attachment=None):
    """Email the team (and acknowledge the sender). Returns True when sent.

    fields     -- list of (label, value) pairs, rendered in order
    attachment -- optional (filename, mimetype, bytes) for the RFP tab
    """
    cfg = _config()
    title, heading, phrase = KIND_LABELS.get(kind, FALLBACK_LABEL)

    # Microsoft Graph is the transport when it is configured; SMTP stays as the
    # fallback, and the local archive catches everything else.
    if graph_mail.configured() and cfg["recipient"]:
        sent = graph_mail.send(
            subject=f"{heading} — {reference}",
            html=_notification_html(kind, fields, reference),
            to=cfg["recipient"],
            reply_to=reply_to,
            attachment=attachment,
        )
        if ack_to:
            try:
                graph_mail.send(
                    subject=f"We have your {phrase} — {reference}",
                    html=_ack_html(ack_name or "there", kind, reference),
                    to=ack_to,
                )
            except Exception:
                logger.exception("Acknowledgement to %s failed (notification was sent).", ack_to)
        _archive(kind, fields, reference, "emailed via Graph" if sent else "Graph send failed; archived only")
        if sent:
            return True
        logger.warning("Graph send failed for %s %s — trying SMTP.", kind, reference)

    if not (cfg["username"] and cfg["password"] and cfg["recipient"]):
        _archive(kind, fields, reference, "SMTP not configured; archived only")
        logger.info("Mail not configured — %s %s archived locally.", kind, reference)
        return False

    msg = EmailMessage()
    msg["Subject"] = f"{heading} — {reference}"
    msg["From"] = formataddr((BRAND, cfg["sender"]))
    msg["To"] = cfg["recipient"]
    msg["Date"] = formatdate(localtime=True)
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(_plain(fields, reference))
    msg.add_alternative(_notification_html(kind, fields, reference), subtype="html")

    if attachment:
        filename, mimetype, payload = attachment
        maintype, _, subtype = mimetype.partition("/")
        msg.add_attachment(payload, maintype=maintype or "application",
                           subtype=subtype or "octet-stream", filename=filename)

    ack = None
    if ack_to:
        ack = EmailMessage()
        ack["Subject"] = f"We have your {phrase} — {reference}"
        ack["From"] = formataddr((BRAND, cfg["sender"]))
        ack["To"] = ack_to
        ack["Date"] = formatdate(localtime=True)
        ack.set_content(
            f"Thank you, {ack_name or 'there'}.\n\n"
            f"We have received your {title.lower()} and will be in touch shortly.\n"
            f"Your reference is {reference}.\n\n{BRAND}"
        )
        ack.add_alternative(_ack_html(ack_name or "there", kind, reference), subtype="html")

    try:
        with smtplib.SMTP(cfg["server"], cfg["port"], timeout=20) as smtp:
            if cfg["tls"]:
                smtp.starttls()
            smtp.login(cfg["username"], cfg["password"])
            smtp.send_message(msg)
            if ack:
                try:
                    smtp.send_message(ack)
                except Exception:
                    logger.exception("Acknowledgement to %s failed (notification was sent).", ack_to)
        logger.info("Emailed %s %s to %s", kind, reference, cfg["recipient"])
        _archive(kind, fields, reference, "emailed")
        return True
    except Exception:
        logger.exception("SMTP send failed for %s %s — archiving locally.", kind, reference)
        _archive(kind, fields, reference, "SMTP send failed; archived only")
        return False
