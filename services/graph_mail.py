"""Outbound mail through Microsoft Graph (Microsoft 365), client-credentials flow.

Replaces the Gmail SMTP transport: the same messages services/mailer.py builds
are handed to Graph's sendMail endpoint, sent as the configured mailbox, and
filed in its Sent Items. Stdlib only — nothing new to install.

Setup (Azure portal -> App registrations -> your app):
  GRAPH_TENANT_ID      Directory (tenant) ID
  GRAPH_CLIENT_ID      Application (client) ID
  GRAPH_CLIENT_SECRET  Certificates & secrets -> New client secret -> the VALUE
  GRAPH_SENDER         the mailbox to send from, e.g. karishma.singh@…

The app also needs the **application** permission Microsoft Graph -> Mail.Send
with admin consent granted. Application permissions reach every mailbox in the
tenant, so scope it down to the one sender with an ApplicationAccessPolicy:

  New-ApplicationAccessPolicy -AppId <client id> -PolicyScopeGroupId <sender> \\
      -AccessRight RestrictAccess -Description "Website enquiry mailer"

Leave any of the four blank and services/mailer.py falls back to SMTP, then to
the local archive — a submission is never lost.
"""

import base64
import json
import logging
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from flask import current_app

logger = logging.getLogger(__name__)

GRAPH = "https://graph.microsoft.com/v1.0"
LOGIN = "https://login.microsoftonline.com"
TIMEOUT = 20
# Graph rejects a sendMail payload over ~4 MB; base64 inflates by a third, so
# anything bigger travels as a link in the mail rather than an attachment.
MAX_ATTACHMENT = 3 * 1024 * 1024

_token = {"value": "", "expires": 0.0}
_lock = threading.Lock()


def config():
    cfg = current_app.config
    return {
        "tenant": cfg.get("GRAPH_TENANT_ID") or "",
        "client": cfg.get("GRAPH_CLIENT_ID") or "",
        "secret": cfg.get("GRAPH_CLIENT_SECRET") or "",
        "sender": cfg.get("GRAPH_SENDER") or "",
    }


def configured():
    return all(config().values())


def _post(url, data, headers, raw=False):
    request = urllib.request.Request(
        url,
        data=data if raw else json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        body = response.read().decode("utf-8", "replace")
        return response.status, body


def access_token(force=False):
    """A cached app-only token; refreshed a minute before it expires."""
    with _lock:
        if not force and _token["value"] and time.time() < _token["expires"]:
            return _token["value"]

        cfg = config()
        form = urllib.parse.urlencode({
            "client_id": cfg["client"],
            "client_secret": cfg["secret"],
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        }).encode()
        _, body = _post(
            f"{LOGIN}/{cfg['tenant']}/oauth2/v2.0/token",
            form,
            {"Content-Type": "application/x-www-form-urlencoded"},
            raw=True,
        )
        payload = json.loads(body)
        _token["value"] = payload["access_token"]
        _token["expires"] = time.time() + int(payload.get("expires_in", 3600)) - 60
        return _token["value"]


def _message(subject, html, to, reply_to=None, attachment=None):
    """Graph sends a single body, so this is the HTML one; the plain-text twin
    services/mailer.py builds is kept for the SMTP path and the local archive."""
    message = {
        "subject": subject,
        "body": {"contentType": "HTML", "content": html},
        "toRecipients": [{"emailAddress": {"address": to}}],
    }
    if reply_to:
        message["replyTo"] = [{"emailAddress": {"address": reply_to}}]
    if attachment:
        filename, mimetype, payload = attachment
        if len(payload) <= MAX_ATTACHMENT:
            message["attachments"] = [{
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": filename,
                "contentType": mimetype or "application/octet-stream",
                "contentBytes": base64.b64encode(payload).decode("ascii"),
            }]
        else:
            logger.info("Attachment %s is %.1f MB — too large for Graph sendMail, sending without it.",
                        filename, len(payload) / 1e6)
    return message


def send(subject, html, to, reply_to=None, attachment=None):
    """Send one message as GRAPH_SENDER. Returns True when Graph accepts it."""
    cfg = config()
    if not configured():
        return False

    payload = {"message": _message(subject, html, to, reply_to, attachment),
               "saveToSentItems": True}
    url = f"{GRAPH}/users/{cfg['sender']}/sendMail"

    for attempt in (1, 2):                      # one retry on an expired token
        try:
            token = access_token(force=attempt == 2)
            status, _ = _post(url, payload, {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            })
            logger.info("Graph sendMail -> %s (HTTP %s)", to, status)
            return True
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:400]
            if exc.code == 401 and attempt == 1:
                continue
            logger.error("Graph sendMail rejected (%s): %s", exc.code, detail)
            return False
        except Exception:
            logger.exception("Graph sendMail failed.")
            return False
    return False


def check():
    """Diagnostics for scripts/graph_mail_test.py: (ok, message)."""
    cfg = config()
    missing = [k for k, v in cfg.items() if not v]
    if missing:
        return False, f"Not configured: missing {', '.join(missing)}."
    try:
        access_token(force=True)
    except urllib.error.HTTPError as exc:
        return False, f"Token request failed: {exc.read().decode('utf-8', 'replace')[:300]}"
    except Exception as exc:
        return False, f"Token request failed: {exc}"

    # Mail.Send alone cannot read the directory, so a 403 here is expected and
    # not a failure — only a missing role is.
    import base64 as _b64

    claims = access_token().split(".")[1]
    claims += "=" * (-len(claims) % 4)
    roles = json.loads(_b64.urlsafe_b64decode(claims)).get("roles", [])
    if "Mail.Send" not in roles:
        return False, ("Token OK, but the app has no Mail.Send application role — add the APPLICATION "
                       "permission Mail.Send and click 'Grant admin consent'. (roles: %s)" % (roles or "none"))

    try:
        request = urllib.request.Request(
            f"{GRAPH}/users/{cfg['sender']}?$select=displayName,mail,userPrincipalName",
            headers={"Authorization": f"Bearer {access_token()}"},
        )
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            info = json.loads(response.read().decode())
        return True, f"Token OK, Mail.Send granted. Sender: {info.get('displayName')} <{info.get('mail') or info.get('userPrincipalName')}>"
    except urllib.error.HTTPError:
        return True, f"Token OK, Mail.Send granted. Sender: {cfg['sender']} (directory read not permitted — expected)"
