"""POST handlers for the three /lets-connect tabs.

All three forms -> Sellsy (services/sellsy.py, background thread, local-file fallback).
RFP upload -> emailed via Microsoft Graph (services/mailer.py), or saved to instance/rfps/ if unset.
Callback request -> logged locally (Teams Bookings / WhatsApp are client-side
links configured via .env; this just captures the "request a callback" path).

Every path renders connect.html directly (not a redirect) so a submitted tab
can show its in-page success panel in place of the form.
"""

import logging
import os
from datetime import datetime, timezone

from flask import current_app, render_template, request

from content import site as site_content
from forms import CallbackForm, EventBriefForm, RfpForm
from services.leads import dispatch_brief, reference_id
from services.mailer import send_inquiry
from services.storage import content_type_for, upload_rfp
from services.store import save_inquiry
from services.visitors import identify
from services.whatsapp import send_inquiry_alert
from services.sellsy import send_to_sellsy

logger = logging.getLogger(__name__)

from flask import Blueprint

inquiry = Blueprint("inquiry", __name__, url_prefix="/inquiry")


def _connect_context(**overrides):
    ctx = {
        "content": site_content.CONNECT,
        "contact": site_content.CONTACT,
        "brief_form": EventBriefForm(),
        "rfp_form": RfpForm(),
        "callback_form": CallbackForm(),
        "teams_booking_url": current_app.config.get("TEAMS_BOOKING_URL"),
        "whatsapp_number": current_app.config.get("WHATSAPP_NUMBER"),
        "active_tab": "brief",
        "reference_id": None,
    }
    ctx.update(overrides)
    return ctx


def _reference_id(prefix):
    return reference_id(prefix)


@inquiry.route("/brief", methods=["POST"])
def brief():
    form = EventBriefForm()
    if form.website.data:
        # Honeypot tripped — pretend success, do nothing.
        return render_template("connect.html", **_connect_context(brief_success=True, reference_id=_reference_id("BRF")))

    if form.validate_on_submit():
        # Same dispatch the chat Project Assistant uses (services/leads.py).
        reference = dispatch_brief({
            "company": form.company.data,
            "contact_name": form.contact_name.data,
            "email": form.email.data,
            "phone": form.phone.data,
            "country": form.country.data,
            "request_type": form.request_type.data,
            "group_size": form.group_size.data,
            "preferred_dates": form.preferred_dates.data,
            "budget": form.budget.data,
            "message": form.message.data,
        }, request=request, source="form")
        return render_template("connect.html", **_connect_context(brief_success=True, reference_id=reference))

    return render_template("connect.html", **_connect_context(brief_form=form, active_tab="brief")), 400


@inquiry.route("/rfp", methods=["POST"])
def rfp():
    form = RfpForm()
    if form.website.data:
        return render_template("connect.html", **_connect_context(rfp_success=True, reference_id=_reference_id("RFP")))

    if form.validate_on_submit():
        reference = _reference_id("RFP")
        _handle_rfp_upload(form, reference)
        return render_template("connect.html", **_connect_context(rfp_success=True, reference_id=reference))

    return render_template("connect.html", **_connect_context(rfp_form=form, active_tab="rfp")), 400


def _handle_rfp_upload(form, reference):
    uploaded = form.rfp_file.data
    filename = uploaded.filename
    payload = uploaded.read()

    mimetype = content_type_for(filename, uploaded.mimetype or "application/octet-stream")
    stored = upload_rfp(reference, filename, payload, mimetype)  # Supabase Storage, or None

    rfp_fields = [
        ("Name", form.name.data),
        ("E-mail", form.email.data),
        ("Company", form.company.data),
        ("Attached file", filename),
        ("File type", mimetype),
        ("File size", len(payload)),
    ]
    if stored:
        rfp_fields += [
            ("File URL", stored["url"]),
            ("File path", f"{stored['bucket']}/{stored['path']}"),
        ]
    # The email also carries a 7-day download link; the database keeps the permanent URL.
    email_fields = rfp_fields + ([("Download (7 days)", stored["signed_url"])] if stored and stored.get("signed_url") else [])
    sent = send_inquiry(
        "rfp", email_fields, reference,
        reply_to=form.email.data,
        ack_to=form.email.data,
        ack_name=form.name.data,
        attachment=(filename, uploaded.mimetype or "application/octet-stream", payload),
    )
    whatsapped = send_inquiry_alert("rfp", rfp_fields, reference)
    save_inquiry("rfp", rfp_fields, reference, sent, whatsapped, request)
    send_to_sellsy("rfp", reference, rfp_fields, attachment=(filename, mimetype, payload),
                   company=form.company.data, name=form.name.data, email=form.email.data)
    identify("rfp", reference, rfp_fields)
    if sent or stored:
        return

    # No storage and no mail — keep the document on disk so nothing is lost.
    rfp_dir = os.path.join(current_app.instance_path, "rfps")
    os.makedirs(rfp_dir, exist_ok=True)
    saved_name = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{filename}"
    with open(os.path.join(rfp_dir, saved_name), "wb") as fh:
        fh.write(payload)
    logger.info("RFP saved locally: %s (%s)", saved_name, reference)


@inquiry.route("/callback", methods=["POST"])
def callback():
    form = CallbackForm()
    if form.website.data:
        return render_template("connect.html", **_connect_context(callback_success=True, reference_id=_reference_id("CALL")))

    if form.validate_on_submit():
        reference = _reference_id("CALL")
        callback_fields = [
            ("Name", form.name.data),
            ("E-mail", form.email.data),
            ("Company", form.company.data),
            ("Phone", form.phone.data),
        ]
        emailed = send_inquiry("callback", callback_fields, reference, reply_to=form.email.data,
                               ack_to=form.email.data, ack_name=form.name.data)
        whatsapped = send_inquiry_alert("callback", callback_fields, reference)
        save_inquiry("callback", callback_fields, reference, emailed, whatsapped, request)
        send_to_sellsy("callback", reference, callback_fields, company=form.company.data,
                       name=form.name.data, email=form.email.data, phone=form.phone.data)
        identify("callback", reference, callback_fields)
        return render_template("connect.html", **_connect_context(callback_success=True, reference_id=reference))

    return render_template("connect.html", **_connect_context(callback_form=form, active_tab="call")), 400
