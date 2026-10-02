"""POST /chat — the site assistant.

Two modes, chosen by the widget:

* ``ask``     — Ask Caraïbes, grounded Q&A (services/ask.py)
* ``project`` — Project Assistant, brief building (services/project_assistant.py)

The browser sends only the transcript; every API key stays on the server, and
the brief is re-derived here from the transcript on each turn, so nothing the
client sends is trusted as a field value. A brief is submitted only when the
request carries ``confirm: true`` — the widget sends that exclusively from the
"Submit my brief" button the visitor clicks after seeing the summary.
"""

import time
from collections import defaultdict, deque

from flask import Blueprint, jsonify, request

from services.ask import reply
from services.project_assistant import respond

chat = Blueprint("chat", __name__)

# Per-visitor throttle: each message can cost an API call, so cap bursts.
RATE_LIMIT = 20          # messages
RATE_WINDOW = 60         # seconds
SUBMIT_LIMIT = 3         # briefs
SUBMIT_WINDOW = 3600     # seconds
_hits = defaultdict(deque)
_submits = defaultdict(deque)


def _allowed(bucket, key, limit, window):
    now = time.monotonic()
    hits = bucket[key]
    while hits and now - hits[0] > window:
        hits.popleft()
    if len(hits) >= limit:
        return False
    hits.append(now)
    return True


def _visitor():
    return request.headers.get("X-Forwarded-For", request.remote_addr or "?").split(",")[0].strip()


@chat.route("/chat", methods=["POST"])
def chat_message():
    if not request.is_json:
        return jsonify(error="Expected JSON."), 415

    visitor = _visitor()
    if not _allowed(_hits, visitor, RATE_LIMIT, RATE_WINDOW):
        return jsonify(reply="You're sending messages quickly — give it a moment and try again.",
                       mode="throttled"), 429

    payload = request.get_json(silent=True) or {}
    messages = payload.get("messages")

    if payload.get("mode") == "project":
        confirm = payload.get("confirm") is True
        if confirm and not _allowed(_submits, visitor, SUBMIT_LIMIT, SUBMIT_WINDOW):
            return jsonify(reply="That's several briefs from here already — the team will be in touch "
                                 "on the first one. Use Let's Connect if you need to send another.",
                           mode="project", ready=False, brief=[]), 429
        return jsonify(respond(messages, confirm=confirm, request=request))

    return jsonify(reply(messages))
